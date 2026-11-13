"""Keep synthetic UI transcripts independent of locally installed host CLIs."""
from unittest.mock import patch

from agent_skills_installer import ui


def run_with_fixture_hosts(catalog, *args, **kwargs):
    """Expose fixture hosts while retaining real lookup for dependency tools."""
    hosts = {spec.host for spec in catalog}
    real_which = ui.shutil.which

    def which(command, *lookup_args, **lookup_kwargs):
        if command in hosts:
            return f'/fixture/bin/{command}'
        return real_which(command, *lookup_args, **lookup_kwargs)

    with patch.object(ui.shutil, 'which', side_effect=which):
        return ui.run(catalog, *args, **kwargs)
