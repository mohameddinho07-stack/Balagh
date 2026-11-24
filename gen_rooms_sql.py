"""Regenerate rooms_v2.sql from the case registry. Run after adding any case."""
from pathlib import Path
from room_catalog import catalog_json


def render(registry=None, generate=None):
    tmpl = (Path(__file__).parent / 'rooms_v2.sql.tmpl').read_text(encoding='utf-8')
    return tmpl.replace('@@CATALOG@@', catalog_json(registry, generate))


if __name__ == '__main__':
    (Path(__file__).parent / 'rooms_v2.sql').write_text(render(), encoding='utf-8')
    print('rooms_v2.sql written')
