from decimal import Decimal
import pytest
from app.workflow import run
from app.modules.m2_mapping.coerce import number
from app.errors import DomainError

def test_thousands():
    # TRAP-06
    assert number('１,２３４.５')==Decimal('1234.5')
def test_missing_numeric():
    # TRAP-07
    with pytest.raises(DomainError) as e:number('N/A')
    assert e.value.code=='MISSING'
def test_identifier_zeroes(raw):
    # TRAP-08
    assert run(raw,{},2)['rows'][0]['id'].startswith('00')
def test_real_missing_quarantine(raw):
    s=run(raw,{},2);assert any(r['code']=='MISSING' for r in s['quarantine'])
def test_real_conflict_quarantine(raw):
    # TRAP-14
    s=run(raw,{},2);assert sum(r['code']=='CONFLICT' for r in s['quarantine'])==2
def test_real_deduplication(raw):
    s=run(raw,{},2);assert s['duplicate_count']==1
def test_decimal_precision():
    # TRAP-10
    assert sum([number('0.1')]*1000)==Decimal('100.0')

def one_row(uncertainty):
    base='id,sample_id,batch,product,analyte,method,version,sampled,reported,result,unit,lod,uncertainty'
    row='00001,S001,B001,苹果,P01,LC-MS/MS,1,2026-08-01,2026-08-02,0.004,mg/kg,0.001,'+uncertainty
    return (base+'\n'+row+'\n').encode()

def test_optional_uncertainty_coerced():
    assert run(one_row('0.002'),{},2)['rows'][0]['uncertainty']=='0.002'
def test_optional_uncertainty_sentinel_is_undeclared():
    s=run(one_row('N/A'),{},2);assert 'uncertainty' not in s['rows'][0] and not s['quarantine']
def test_optional_uncertainty_empty_is_undeclared():
    s=run(one_row(''),{},2);assert 'uncertainty' not in s['rows'][0] and not s['quarantine']
def test_optional_uncertainty_invalid_quarantined():
    s=run(one_row('abc'),{},2);assert not s['rows'] and s['quarantine'][0]['code']=='NUMBER'
