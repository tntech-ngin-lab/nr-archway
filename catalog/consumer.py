import logging
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name
from argparse import ArgumentParser, SUPPRESS

logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

async def catalog_consumer(app:NDNApp, name:Name):
    try:
        logging.info(f'Expressing Interest {Name.to_str(name)}')
        data_name, meta_info, content = await app.express_interest(name, must_be_fresh=True, can_be_prefix=False, lifetime=6000)
        logging.info(f'Received Data Name: {Name.to_str(data_name)}')
        logging.info(f'\t{meta_info}')
        if content:
            logging.info(f'\tContent: {bytes(content).decode()}')
        else:
            logging.info(f'\tContent: None')
    except InterestNack as e:
        logging.warning(f'Nacked with reason={e.reason}')
    except InterestTimeout:
        logging.warning(f'Timeout')
    except InterestCanceled:
        logging.warning(f'Canceled')
    except ValidationFailure:
        logging.warning(f'Data failed to validate')
    finally:
        app.shutdown()

def main():
    # Command Line Parser
    parser = ArgumentParser(add_help=False,description="Request an Interest")
    requiredArgs = parser.add_argument_group("required arguments")
    optionalArgs = parser.add_argument_group("optional arguments")
    # Adding All Command Line Arguments
    requiredArgs.add_argument("-n","--name",required=True,help="name of the interest")
    optionalArgs.add_argument("-h","--help",action="help",default=SUPPRESS,help="show this help message and exit")
    # Getting All Arugments
    args = vars(parser.parse_args())
    name = Name.from_str('/catalog') + Name.from_str(args["name"])
    app = NDNApp()
    try:
        app.run_forever(after_start=catalog_consumer(app, name))
    except FileNotFoundError:
        logging.warning(f'Error: could not connect to NFD')

if __name__ == '__main__':
    main()