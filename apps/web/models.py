"""Load the domain models into the existing Django registry."""

from apps.accounts import models as accounts_models  # noqa: F401
from apps.teams import models as teams_models  # noqa: F401
from apps.wallet import models as wallet_models  # noqa: F401
from apps.missions import models as missions_models  # noqa: F401
from apps.questions import models as questions_models  # noqa: F401
from apps.competitions import models as competitions_models  # noqa: F401
from apps.treasure import models as treasure_models  # noqa: F401
