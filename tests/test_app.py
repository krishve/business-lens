from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('year',[2021,2025])
def test_all_pages_render(year):
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    app.sidebar.selectbox[0].select(year).run()
    for view in ['Business overview','Customers','Services','Support insights','Product quality','Support team','FAQ opportunities','Data & definitions']:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception, (view,[x.message for x in app.exception])


def test_upload_replaces_sample_and_reports_missing_files():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Upload CSV files').run()
    files=[(p.name,p.read_bytes(),'text/csv') for p in sorted((ROOT/'data'/'sample').glob('*.csv'))]
    app.sidebar.file_uploader[0].set_value(files).run()
    assert not app.exception
    assert not app.error
    assert app.metric[0].value=='$2,998,541'
    app.sidebar.file_uploader[0].set_value(files[:-1]).run()
    assert app.error
    assert not app.exception
