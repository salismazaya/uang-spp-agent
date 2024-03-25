from typing import Any
from django.core.management import BaseCommand

from neonize.client import NewClient
from neonize.events import (
    ConnectedEv,
    MessageEv,
    PairStatusEv,
    ReceiptEv,
    CallOfferEv,
)
from neonize.utils import log

from core.ai import Conversation

client = NewClient("session.db")


@client.event(ConnectedEv)
def on_connected(_: NewClient, __: ConnectedEv):
    log.info("⚡ Connected")


@client.event(ReceiptEv)
def on_receipt(_: NewClient, receipt: ReceiptEv):
    log.debug(receipt)


@client.event(CallOfferEv)
def on_call(_: NewClient, call: CallOfferEv):
    log.debug(call)


@client.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    handler(client, message)


def handler(client: NewClient, message: MessageEv):
    text = message.Message.conversation or message.Message.extendedTextMessage.text
    chat = message.Info.MessageSource.Chat
    
    conversation = Conversation.get_conversation(chat.User)
    answer = conversation(text)

    client.send_message(chat, answer)

@client.event(PairStatusEv)
def PairStatusMessage(_: NewClient, message: PairStatusEv):
    log.info(f"logged as {message.ID.User}")


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        client.connect()