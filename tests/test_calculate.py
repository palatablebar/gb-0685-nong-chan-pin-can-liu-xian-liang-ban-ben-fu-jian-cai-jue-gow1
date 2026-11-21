from copy import deepcopy
from app.workflow import run
from app.modules.m5_calculate.rules import select_reports,apply

def test_real_retest_replaces_initial(raw):
    s=run(raw,{});assert len(s['calculations'])==24 and s['calculations'][0]['id']=='00002' and s['calculations'][0]['replaces']=='00001'
def test_real_other_analyte_not_erased(raw):
    s=run(raw,{});assert s['business']=={'total':24,'pass':11,'fail':12,'uncertain':1,'released':23,'held':1,'unit':'检测项目'}
def test_wrong_sample_reference_rejected(raw):
    s=run(raw,{},4);s['measurements'][1]['sample_id']='OTHER';chosen,bad=select_reports(s['measurements']);assert bad['00002']=='REFERENCE' and any(r['id']=='00001' for r in chosen)
def test_wrong_method_reference_rejected(raw):
    s=run(raw,{},4);s['measurements'][1]['method']='GC-MS';_,bad=select_reports(s['measurements']);assert bad['00002']=='REFERENCE'
def test_future_reference_rejected(raw):
    s=run(raw,{},4);s['measurements'][1]['reported']='2026-08-01';_,bad=select_reports(s['measurements']);assert bad['00002']=='REFERENCE'
def test_cycle_rejected(raw):
    # TRAP-20
    s=run(raw,{},4);s['measurements'][0]['relation']='00002';_,bad=select_reports(s['measurements']);assert '00001' in bad and '00002' in bad
def test_input_order_cannot_change_verdict(raw):
    a=run(raw,{},4);b=deepcopy(a);b['measurements'].reverse();ca,ba=select_reports(a['measurements']);cb,bb=select_reports(b['measurements']);assert sorted(r['id'] for r in ca)==sorted(r['id'] for r in cb) and ba==bb


def test_same_report_id_latest_revision_is_authoritative(raw):
    s=run(raw,{},4);new=dict(s['measurements'][1],version='3',lower='0.006',upper='0.006',code='FAIL');s['measurements'].append(new);chosen,bad=select_reports(s['measurements'])
    assert next(r for r in chosen if r['id']=='00002')['code']=='FAIL' and '00002' not in bad

def test_borderline_project_held_not_released(raw):
    # 复检0.004贴限量0.005，扩展不确定度0.002使区间越限：暂缓待补而非确定结论
    s=run(raw,{});c=next(r for r in s['calculations'] if r['id']=='00002')
    assert c['code']=='UNCERTAIN' and c['decision']=='HOLD' and c['value']=='0.004' and c['uncertainty']=='0.002' and c['result']=='0.004'

def test_held_project_does_not_hold_batch_mates(raw):
    s=run(raw,{})
    batch={r['id']:r for r in s['calculations'] if r['batch']=='B001'}
    assert batch['00002']['decision']=='HOLD' and batch['00003']['decision']=='RELEASE' and batch['00005']['decision']=='RELEASE'

def test_failed_supplement_keeps_old_version(raw):
    # 证据补齐报告越过样本关联被隔离，旧版结论与原值、不确定度保留
    s=run(raw,{},4);s['measurements'].append(dict(s['measurements'][1],id='00910',relation='00002',sample_id='OTHER',_line=900))
    apply(s);c=next(r for r in s['calculations'] if r['sample_id']=='S001' and r['analyte']=='P01')
    assert c['id']=='00002' and c['uncertainty']=='0.002' and any(q['id']=='00910' and q['code']=='REFERENCE' for q in s['quarantine'])

def test_valid_supplement_replaces_and_releases(raw):
    s=run(raw,{},4);s['measurements'].append(dict(s['measurements'][1],id='00910',relation='00002',reported='2026-08-04',version='1',lower='0.0035',upper='0.0045',code='PASS',uncertainty='0.0005',_line=900))
    apply(s);c=next(r for r in s['calculations'] if r['sample_id']=='S001' and r['analyte']=='P01')
    assert c['id']=='00910' and c['replaces']=='00002' and c['decision']=='RELEASE' and s['business']['held']==0

def test_same_source_rerun_adds_no_project(raw):
    a=run(raw,{});b=run(raw,{})
    assert a['run_id']==b['run_id'] and len(b['calculations'])==len(a['calculations'])==24

def test_duplicate_retest_row_adds_no_project(raw):
    row=[l for l in raw.decode('utf-8-sig').split('\r\n') if l.startswith('00002,')][0]
    s=run(raw+row.encode(),{})
    assert len(s['calculations'])==24 and s['duplicate_count']==2
