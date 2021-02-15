import logging
import ndn.utils
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name, Component, InterestParam
from argparse import ArgumentParser, SUPPRESS

logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

app = NDNApp()

async def main():
    try:
        # Command Line Parser
        parser = ArgumentParser(add_help=False,description="Request an Interest")
        requiredArgs = parser.add_argument_group("required arguments")
        optionalArgs = parser.add_argument_group("optional arguments")
        # Adding All Command Line Arguments
        requiredArgs.add_argument("-n","--name",required=True,help="name of the interest")
        optionalArgs.add_argument("-h","--help",action="help",default=SUPPRESS,help="show this help message and exit")
        # Getting All Arugments
        args = vars(parser.parse_args())

        app_param = args["name"]+"/seg0"
        timestamp = ndn.utils.timestamp()
        name = Name.from_str('/catalog') + [Component.from_timestamp(timestamp)]
        print(f'Sending Interest {Name.to_str(name)}, '
                f'{InterestParam(must_be_fresh=True, lifetime=6000)}, '
              f'{app_param}')
        data_name, meta_info, content = await app.express_interest(
            name, app_param.encode(), must_be_fresh=True, can_be_prefix=False, lifetime=6000)

        print(f'Received Data Name: {Name.to_str(data_name)}')
        print(meta_info)
        if content:
            print(f'Content: {bytes(content).decode()}')
        else:
            print(f'Content: None')
    except InterestNack as e:
        print(f'Nacked with reason={e.reason}')
    except InterestTimeout:
        print(f'Timeout')
    except InterestCanceled:
        print(f'Canceled')
    except ValidationFailure:
        print(f'Data failed to validate')
    finally:
        app.shutdown()


if __name__ == '__main__':
    app.run_forever(after_start=main())