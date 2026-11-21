import pytest
from app.workflow import run
from app.modules.m4_segments.rules import concentration
from app.errors import DomainError

def test_detection_interval_crosses_limit():
    r=concentration('<0.01','mg/kg','0.01','0.005');assert r['code']=='UNCERTAIN' and r['lower']=='0' and r['upper']=='0.01'
def test_detection_interval_below_limit():assert concentration('<0.01','mg/kg','0.01','0.01')['code']=='PASS'
def test_unit_conversion():
    # TRAP-15
    r=concentration('30','ug/kg','1','0.02');assert r['upper']=='0.030' and r['code']=='FAIL'
def test_numeric_equal_limit_passes():assert concentration('0.005','mg/kg','0.001','0.005')['code']=='PASS'
def test_real_initial_uncertain(raw):assert run(raw,{},4)['measurements'][0]['code']=='UNCERTAIN'
def test_real_second_pesticide_exceeds(raw):assert run(raw,{},4)['measurements'][2]['code']=='FAIL'
def test_lod_inconsistent_rejected():
    with pytest.raises(DomainError):concentration('<0.01','mg/kg','0.02','0.005')

def test_uncertainty_crossing_limit_is_uncertain():
    r=concentration('0.004','mg/kg','0.001','0.005','0.002')
    assert r['code']=='UNCERTAIN' and r['lower']=='0.002' and r['upper']=='0.006' and r['value']=='0.004' and r['uncertainty']=='0.002'
def test_uncertainty_within_limit_still_passes():assert concentration('0.004','mg/kg','0.001','0.005','0.0005')['code']=='PASS'
def test_uncertainty_fail_stays_fail():
    r=concentration('30','ug/kg','1','0.02','5');assert r['code']=='FAIL' and r['lower']=='0.025' and r['uncertainty']=='0.005'
def test_uncertainty_undeclared_keeps_point_value():
    r=concentration('0.004','mg/kg','0.001','0.005');assert r['code']=='PASS' and r['uncertainty'] is None and r['value']=='0.004'
def test_uncertainty_on_censored_recorded_not_applied():
    r=concentration('<0.01','mg/kg','0.01','0.005','0.003')
    assert r['lower']=='0' and r['upper']=='0.01' and r['value'] is None and r['uncertainty']=='0.003'
def test_uncertainty_lower_bound_floored_at_zero():assert concentration('0.004','mg/kg','0.001','0.005','0.01')['lower']=='0'
def test_uncertainty_negative_rejected():
    with pytest.raises(DomainError) as e:concentration('0.004','mg/kg','0.001','0.005','-0.1')
    assert e.value.code=='RANGE'
def test_uncertainty_unparseable_rejected():
    with pytest.raises(DomainError) as e:concentration('0.004','mg/kg','0.001','0.005','abc')
    assert e.value.code=='NUMBER'
