from slave_server import SlaveServer
from utils.logger import get_logger

logger = get_logger('slave')

def main():
    try:
        logger.info('Starting slave server...')
        server = SlaveServer()
        server.run()
    except Exception as e:
        logger.error(f'Server failed to start: {e}')
        raise

if __name__ == '__main__':
    main() 