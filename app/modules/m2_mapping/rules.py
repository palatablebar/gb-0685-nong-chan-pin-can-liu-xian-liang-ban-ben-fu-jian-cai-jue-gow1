from copy import deepcopy
from app.config import REQUIRED,NUMERIC,OPTIONAL_NUMERIC,DATES,TIMES
from app.errors import DomainError
from app.modules.m2_mapping.coerce import number,day,instant,SENTINELS

def normalize(state):
    state=deepcopy(state);good=[];groups={}
    for row in state['rows']:
        try:
            for field in REQUIRED:
                if str(row.get(field,'')).strip().upper() in SENTINELS:raise DomainError('MISSING','必填值缺失')
            item=dict(row)
            for field in NUMERIC:
                if field in item and item[field] != '':item[field]=number(item[field])
            for field in DATES:
                if field in item and item[field] != '':item[field]=day(item[field])
            for field in TIMES:
                if field in item and item[field] != '':item[field]=instant(item[field])
            # Optional numerics (e.g. expanded uncertainty): a sentinel means "not
            # declared", never zero; an unparseable value quarantines the row.
            for field in OPTIONAL_NUMERIC:
                if field in item:
                    if str(item[field]).strip().upper() in SENTINELS:del item[field]
                    else:item[field]=number(item[field])
            key=(item['id'],str(item.get('version','1')))
            groups.setdefault(key,[]).append(item)
        except DomainError as error:state['quarantine'].append({'line':row['_line'],'id':row.get('id',''),'code':error.code,'raw':row['_raw']})
    for key,rows in groups.items():
        unique={str(sorted((k,str(v)) for k,v in r.items() if not k.startswith('_'))) for r in rows}
        if len(unique)>1:
            for r in rows:state['quarantine'].append({'line':r['_line'],'id':r['id'],'code':'CONFLICT','raw':r['_raw']})
        else:
            good.append(rows[0]);state['duplicate_count']+=len(rows)-1
    state['rows']=good
    return state
