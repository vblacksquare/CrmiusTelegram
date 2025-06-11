
import urllib.parse
from dtypes.user import CrmUser
from dtypes.group import Group

from config import get_config


def generate_group_app_link(
    reciever: CrmUser,
    forward_to: CrmUser,
    group: Group,
) -> str:

    resource_link = get_config().crm.group_chat_url.format(name=group.slug)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = forward_to if forward_to else reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


def generate_private_app_link(
    sender: CrmUser,
    reciever: CrmUser,
    forward_to: CrmUser
) -> str:

    resource_link = get_config().crm.private_chat_url.format(username=sender.username)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = forward_to if forward_to else reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)

