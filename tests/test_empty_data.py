from pathlib import Path
from streamlit.testing.v1 import AppTest
from data_loader import read_files
from metrics import annual_results

ROOT=Path(__file__).resolve().parents[1]


def test_header_only_transaction_inputs():
    masters={'periods','customers','customer_years','staff','releases','topics'}
    files=[]
    for p in sorted((ROOT/'data'/'sample').glob('*.csv')):
        content=p.read_bytes()
        if p.stem not in masters:
            content=content.splitlines()[0]+b'\n'
        files.append((p.name,content))
    data=read_files(files)
    annual=annual_results(data)
    assert annual.Revenue.sum()==0
    assert annual['Operating margin %'].isna().all()
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Upload CSV files').run()
    app.sidebar.radio[1].set_value('Business overview').run()
    app.sidebar.file_uploader[0].set_value([(n,b,'text/csv') for n,b in files]).run()
    for view in ['Ask Lenny','Business overview','Customers','Services','Support insights','Product quality','Support team','FAQ opportunities','Data & definitions']:
        app.sidebar.radio[1].set_value(view).run()
        assert not app.exception, (view,[x.message for x in app.exception])
