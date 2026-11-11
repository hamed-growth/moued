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
    def test_legacy_imports_are_the_same_operations(self):
        pairs = [
            ('missions.services.treasure', 'apps.treasure.services.checkout', ['InsufficientPoints', 'OutOfStock', 'purchase_treasure_item']),
            ('missions.services.mission_review', 'apps.missions.services.review', ['approve_mission_request', 'reject_mission_request']),
            ('missions.services.competitions', 'apps.competitions.services.rewards', ['finalize_competition', 'finish_competition_registration']),
            ('missions.selectors.profiles', 'apps.accounts.selectors.profiles', ['get_profile_rank', 'get_profile_history']),
            ('missions.selectors.leagues', 'apps.teams.selectors.leagues', ['get_profile_team_leaderboard', 'get_league_rankings', 'get_ranked_teams']),
        ]
        for old, new, names in pairs:
            legacy, domain = importlib.import_module(old), importlib.import_module(new)
            for name in names:
                with self.subTest(name=name):
                    self.assertIs(getattr(legacy, name), getattr(domain, name))

    def test_model_fields_tables_and_user_identity_are_unchanged(self):
        self.assertEqual(settings.AUTH_USER_MODEL, BASELINE['auth'])
        self.assertEqual(settings.INSTALLED_APPS, BASELINE['apps'])
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
        self.assertEqual(actual, BASELINE['models'])

    def test_url_and_admin_contracts_are_unchanged(self):
        from django.contrib import admin
        routes = []
        def walk(patterns, prefix='', namespace=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    walk(pattern.url_patterns, prefix + str(pattern.pattern), namespace + (pattern.namespace + ':' if pattern.namespace else ''))
                else:
                    routes.append([prefix + str(pattern.pattern), namespace + (pattern.name or ''), pattern.lookup_str])
        walk(get_resolver().url_patterns)
        # Django's test runner disables DEBUG, so development media serving is absent.
        public_routes = lambda rows: [r for r in rows if r[2] != 'django.views.static.serve']
        self.assertEqual(public_routes(routes), public_routes(BASELINE['urls']))
        self.assertEqual(sorted(m._meta.label for m in admin.site._registry), BASELINE['admin'])

    def test_domain_imports_have_no_presentation_or_legacy_dependencies(self):
        root = Path(__file__).resolve().parents[1]
        forbidden = ('dashboard', 'missions.views', 'missions.services', 'missions.selectors', 'django.http', 'django.shortcuts', 'django.template')
        graph = {}
        for path in (root / 'apps').rglob('*.py'):
            module = '.'.join(path.relative_to(root).with_suffix('').parts)
            package = module if path.name == '__init__.py' else module.rpartition('.')[0]
            graph[module] = set()
            for node in ast.walk(ast.parse(path.read_text(encoding='utf8'))):
                targets = []
                if isinstance(node, ast.Import): targets = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    target = node.module or ''
                    if node.level:
                        target = importlib.util.resolve_name('.' * node.level + target, package)
                    targets = [target]
                for target in targets:
                    self.assertFalse(any(target == f or target.startswith(f + '.') for f in forbidden), (module, target))
                    graph[module].add(target)
        def visit(node, stack):
            self.assertNotIn(node, stack, f'Domain import cycle: {stack} -> {node}')
            for target in graph.get(node, ()):
                if target in graph: visit(target, stack + [node])
        for node in graph: visit(node, [])
