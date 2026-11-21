from decimal import Decimal,InvalidOperation
import unicodedata
from app.errors import DomainError
from app.modules.m2_mapping.coerce import SENTINELS

def declared(uncertainty,factor):
    # Expanded uncertainty is optional: absent or sentinel means not declared.
    if uncertainty is None:return None
    text=unicodedata.normalize('NFKC',str(uncertainty)).strip().replace(',','')
    if not text or text.upper() in SENTINELS:return None
    try:spread=Decimal(text)
    except InvalidOperation:raise DomainError('NUMBER','扩展不确定度无法解析')
    if not spread.is_finite() or spread<0:raise DomainError('RANGE','扩展不确定度无效')
    return spread*factor

def concentration(result,unit,lod,limit,uncertainty=None):
    factors={'mg/kg':Decimal(1),'ppm':Decimal(1),'ug/kg':Decimal('.001'),'ppb':Decimal('.001')}
    if unit not in factors:raise DomainError('UNIT','检出量单位无效')
    factor=factors[unit];detection=Decimal(str(lod))*factor;threshold=Decimal(str(limit))
    spread=declared(uncertainty,factor)
    text=unicodedata.normalize('NFKC',str(result)).strip().upper()
    try:
        if text=='ND':lower,upper,exclusive=Decimal(0),detection,True;point=None
        elif text.startswith('<'):
            value=Decimal(text[1:])*factor
            if not value.is_finite() or value<=0 or value!=detection:raise DomainError('RANGE','低于检出限报告与LOD不一致')
            lower,upper,exclusive=Decimal(0),value,True;point=None
        else:
            value=Decimal(text.replace(',',''))*factor
            if not value.is_finite() or value<0 or value<detection:raise DomainError('RANGE','定量值低于检出限')
            point=value
            # Guard band: a declared uncertainty widens the decision interval to
            # [value-U, value+U]; the lower bound is floored at zero.
            if spread is None:lower,upper,exclusive=value,value,False
            else:lower,upper,exclusive=max(Decimal(0),value-spread),value+spread,False
    except InvalidOperation:raise DomainError('NUMBER','检出量无法解析')
    code='PASS' if upper<=threshold else 'FAIL' if lower>threshold else 'UNCERTAIN'
    return {'lower':str(lower),'upper':str(upper),'upper_exclusive':exclusive,'limit':str(threshold),'code':code,'unit':'mg/kg','value':None if point is None else str(point),'uncertainty':None if spread is None else str(spread)}

def apply(state):
    measurements=[];bad=[]
    for r in state['reports']:
        try:
            m=dict(r);m.update(concentration(r['result'],r['unit'],r['lod'],r['limit'],r.get('uncertainty')));measurements.append(m)
        except DomainError as e:bad.append((r,e.code))
    lines={r['_line'] for r,_ in bad};state['rows']=[r for r in state['rows'] if r['_line'] not in lines]
    for r,c in bad:state['quarantine'].append({'line':r['_line'],'id':r['id'],'code':c,'raw':r['_raw']})
    state['measurements']=measurements;return state
