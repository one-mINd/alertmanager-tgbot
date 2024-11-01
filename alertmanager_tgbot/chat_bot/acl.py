"""Access Controles Lists"""

from conf import ACL


def is_operation_permitted(requester: str, operation: str) -> bool:
    """
    Method for check permissions before execute command
    args:
        requester: Telegram nickname who try to execute command
        operation: Type of operation
    """
    if requester in ACL.keys() \
        and operation in ACL.get(requester):
        return True

    return False
