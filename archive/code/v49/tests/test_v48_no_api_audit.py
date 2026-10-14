"""The prepared repair profile uses canonical sources and no provider phases."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from test_v46_no_api_audit import prepared

TOOL=Path(__file__).resolve().parents[1]/'development_tools/audit_v48_no_api.py'

@pytest.mark.parametrize('nomination',['none','model'])
def test_prepared_repair_audit_checks_nomination_identity(tmp_path,approved_state,nomination):
    evaluation=prepared(tmp_path,approved_state);path=evaluation/'DEV_PREP_MANIFEST.json'
    cfg=json.loads(path.read_text());cfg.update(kind='DEVELOPMENT_ONLY_V48_EVENT_EVIDENCE_REPAIR_COMPARISON',
        investigation_profile='event-evidence-repair',nomination_mode=nomination)
    path.write_text(json.dumps(cfg))
    result=subprocess.run([sys.executable,str(TOOL),'--evaluation',str(evaluation)],capture_output=True,text=True)
    if nomination=='model':assert result.returncode!=0
    else:
        assert result.returncode==0,result.stderr
        report=json.loads(result.stdout)
        assert report['provider_calls']==report['mock_nomination_requests']==0
        assert report['mock_transport_calls']==1 and report['gold_labels_read'] is False
        assert report['investigation_profile']=='event-evidence-repair'
