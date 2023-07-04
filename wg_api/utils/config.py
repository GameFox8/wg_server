
SERVER_IP = '192.168.1.200'

DEFAULT_POST_UP = [
    'nft add element inet wg-table interfaces { %i }',
]

DEFAULT_POST_DOWN = [
    'nft delete element inet wg-table interfaces { %i }',
]
