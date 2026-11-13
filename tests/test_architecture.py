"""Guard legacy imports, model identity and the direction of domain dependencies."""
import ast
import importlib
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db.migrations.state import ModelState
from django.db.migrations.writer import MigrationWriter
from django.test import SimpleTestCase
from django.urls import URLResolver, get_resolver

BASELINE = json.loads(Path(__file__).with_name('contract_baseline.json').read_text(encoding='utf8'))

class ArchitectureContracts(SimpleTestCase):
    def test_models_live_in_their_domain_packages(self):
        domains = {
            'accounts': ('User',),
            'teams': ('Team', 'TeamMember'),
            'wallet': ('PointTransaction',),
            'missions': ('MissionCategory', 'Mission', 'TeamMission', 'MissionCompletion', 'MissionRequest'),
            'questions': ('Question', 'DailyQuestion', 'DailyQuestionAnswer'),
            'competitions': ('Competition', 'CompetitionQuestion', 'CompetitionRegistration', 'CompetitionAnswer'),
            'treasure': ('TreasureCategory', 'TreasureItem', 'TreasurePurchase'),
        }
        for domain, models in domains.items():
            for name in models:
                self.assertEqual(apps.get_model('missions', name).__module__, f'apps.{domain}.models')
        for obsolete in ('missions', 'dashboard'):
            self.assertIsNone(importlib.util.find_spec(obsolete))

    def test_model_fields_tables_and_user_identity_are_unchanged(self):
        self.assertEqual(settings.AUTH_USER_MODEL, BASELINE['auth'])
        registered_names = [
            c.label if c.name in ('apps.web', 'apps.backoffice') else c.name
            for c in apps.get_app_configs()
        ]
        self.assertEqual(registered_names, BASELINE['apps'])
        self.assertEqual(apps.get_app_config('missions').name, 'apps.web')
        self.assertEqual(apps.get_app_config('dashboard').name, 'apps.backoffice')
        actual = {}
        for model in apps.get_models():
            state = ModelState.from_model(model)
            actual[model._meta.label] = {
                'table': model._meta.db_table,
                'fields': {n: MigrationWriter.serialize(f)[0] for n,f in state.fields.items()},
                'options': MigrationWriter.serialize(state.options)[0],
                'bases': MigrationWriter.serialize(state.bases)[0],
                'managers': MigrationWriter.serialize(state.managers)[0],
            }
        for name in ('missions.TreasureItem', 'missions.TreasurePurchase'):
            actual.pop(name)
        expected = dict(BASELINE['models'])
        for name in ('missions.TreasureItem', 'missions.TreasurePurchase'):
            expected.pop(name)
        self.assertEqual(actual, expected)

    def test_url_and_admin_contracts_are_unchanged(self):
        from django.contrib import admin
        routes = []
        def walk(patterns, prefix='', namespace=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    walk(pattern.url_patterns, prefix + str(pattern.pattern), namespace + (pattern.namespace + ':' if pattern.namespace else ''))
                else:
                    callback = pattern.lookup_str
                    if callback.startswith('apps.') and '.admin.' in callback:
                        callback = 'missions.admin.' + callback.split('.admin.', 1)[1]
                    elif callback.startswith('apps.'):
                        surface = 'dashboard.views' if '.staff_views.' in callback else 'missions.views'
                        callback = surface + '.' + callback.rsplit('.', 1)[1]
                    routes.append([prefix + str(pattern.pattern), namespace + (pattern.name or ''), callback])
        walk(get_resolver().url_patterns)
        # Django's test runner disables DEBUG, so development media serving is absent.
        public_routes = lambda rows: [r for r in rows if r[2] != 'django.views.static.serve']
        self.assertEqual(
            [r for r in public_routes(routes) if r[1] != 'dashboard:treasure_purchase_reject'],
            public_routes(BASELINE['urls']),
        )
        self.assertEqual(sorted(m._meta.label for m in admin.site._registry), BASELINE['admin'])

    def test_domain_imports_have_no_presentation_or_legacy_dependencies(self):
        root = Path(__file__).resolve().parents[1]
        forbidden = ('dashboard', 'missions', 'django.http', 'django.shortcuts', 'django.template')
        graph = {}
        for path in (root / 'apps').rglob('*.py'):
            if path.name != 'models.py' and path.parent.name not in ('services', 'selectors'):
                continue
            module = '.'.join(path.relative_to(root).with_suffix('').parts)
            package = module if path.name == '__init__.py' else module.rpartition('.')[0]
            graph[module] = set()
            tree = ast.parse(path.read_text(encoding='utf8'))
            for node in ast.walk(tree):
                targets = []
                if isinstance(node, ast.Import): targets = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    target = node.module or ''
                    if node.level:
                        target = importlib.util.resolve_name('.' * node.level + target, package)
                    targets = [target]
                for target in targets:
                    self.assertFalse(any(target == f or target.startswith(f + '.') for f in forbidden), (module, target))
                    self.assertFalse(target.endswith(('.views', '.staff_views', '.admin')), (module, target))
                    if node in tree.body:
                        graph[module].add(target)
        def visit(node, stack):
            self.assertNotIn(node, stack, f'Domain import cycle: {stack} -> {node}')
            for target in graph.get(node, ()):
                if target in graph: visit(target, stack + [node])
        for node in graph: visit(node, [])
