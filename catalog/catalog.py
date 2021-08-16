from typing import Optional
from ndn.app import NDNApp
from ndn.encoding import Name, Component, InterestParam, BinaryStr, FormalName, MetaInfo
from bidirdict import BidirDict
import logging
import pandas as pd
import sys

logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

app = NDNApp()
table = {}
df = pd.read_spss('table.sav')
logging.info(f'NDN Catalog Startup')
logging.info(f'Loading {len(df.index)} translations...')
for i in range(len(df.index)):
    logging.info(f"* translated {df.loc[i,'name']} = {df.loc[i,'interface']},{df.loc[i,'host']},{df.loc[i,'filename']},{df.loc[i,'username']},{df.loc[i,'password']}")
    table[df.loc[i,'name']] = df.loc[i,'interface']+","+df.loc[i,'host']+","+df.loc[i,'filename']+","+df.loc[i,'username']+","+df.loc[i,'password']
logging.info(f'Loading Complete')

@app.route('/catalog')
def on_interest(name: FormalName, param: InterestParam, app_param: Optional[BinaryStr]):
    logging.info(f'Received an Interest')
    print(f'\n>> I: {Name.to_str(name)}, {param}, {Name.to_str(app_name) if app_param else None}')
    print(f'\tTranslating {Name.to_str(name[1:])}')
    s = table.get(Name.to_str(name[1:]))
    content = str(s).encode() if s else None
    app.put_data(name, content=content, freshness_period=500, final_block_id=None)
    print(f'<< D: {Name.to_str(name)}')
    print(f'\t{MetaInfo(freshness_period=500, final_block_id=None)}')
    print(f'\tContent: {s}\n')
    logging.info(f'Served appropriate Translation Data')

def main():
    logging.info(f'listening to prefix /catalog')
    try:
        app.run_forever()
    except FileNotFoundError:
        logging.warning(f'Error: could not connect to NFD')

if __name__ == "__main__":
    sys.exit(main())