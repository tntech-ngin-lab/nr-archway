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
table = BidirDict()

# Openning a Sav File and Populating the Table
df = pd.read_spss('test_table.sav')
for i in range(len(df.index)):
    table[df.loc[i,'i_names']] = df.loc[i,'i_commands']

@app.route('/catalog')
def on_interest(name: FormalName, param: InterestParam, app_param: Optional[BinaryStr]):
    app_param = bytes(app_param).decode()
    app_name_segment_number = Name.from_str(app_param)[-1]
    app_name = Name.from_str(app_param)[:-1]
    print("\n")
    logging.info(f'Received an Interest')
    print(f'>> I: {Name.to_str(name)}, {param}, {Name.to_str(app_name)}')
    if not app_param:
        print("<< No application parameter, dropped")
        return

    s = table.get(Name.to_str(app_name))
    content = str(s).encode()

    app.put_data(name, content=content, freshness_period=500, final_block_id=app_name_segment_number)
    print(f'<< D: {Name.to_str(name)}')
    print(MetaInfo(freshness_period=500, final_block_id=app_name_segment_number))
    print(f'Content: {s}')

def main():
    logging.info(f'NDN Catalog Startup')
    logging.info(f'listening to /catalog')
    app.run_forever()

if __name__ == "__main__":
    sys.exit(main())