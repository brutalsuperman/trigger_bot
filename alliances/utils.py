from alliances.models import Alliances, Spot
from peewee import IntegrityError


def create_spot(name, code, spot_type, chat_id):
    chat_id = -1001168950089
    try:
        spot = Spot.create(
            name=name, code=code, spot_type=spot_type, chat_id=chat_id)
    except IntegrityError:
        return False
    return spot


def get_spot_by_name(name):
    spot = Spot.get_or_none(name=name)
    return spot


def get_all_ali_spots(chat_id=None):
    chat_id = -1001168950089
    if chat_id:
        spots = Spot.select().where(Spot.chat_id == chat_id)
    return spots or None


def delete_ali_spot(chat_id, code_spot):
    chat_id = -1001168950089
    spot = Spot.get_or_none(chat_id=chat_id, code=code_spot)
    if spot:
        spot.delete_instance()
        return True
    return False


def del_spot_by_name(spot_name):
    spot = Alliances.get_or_none(name=spot_name)
    if spot:
        spot.delete_instance()
        return True
    return False


def create_alliances_spot(alliance, guild, date, type=None):
    created = Alliances.insert(name=guild, alliance=alliance, date=date, type=type).on_conflict(
        conflict_target=(Alliances.name),
        preserve=(Alliances.name),
        update={
            "alliance": alliance,
            "date": date}).execute()

    return created


def get_all_alliances(alliance=None, type=None):
    alliance_guilds = None
    if alliance:
        alliance_guilds = Alliances.select(Alliances, Spot).join(
            Spot, on=(Alliances.alliance == Spot.name), attr='extra').where(
                Alliances.alliance == alliance, Alliances.type == type).order_by(
                    Alliances.date.desc())
    else:
        alliance_guilds = Alliances.select(Alliances, Spot).join(
            Spot, on=(Alliances.alliance == Spot.name), attr='extra').where(
                Alliances.type == type).order_by(
                    Alliances.date.desc())
    return alliance_guilds


def delete_spot(alliance, name, type='spot'):
    spot = Alliances.get_or_none(alliance=alliance, name=name, type=type)
    if spot:
        spot.delete_instance()
        return True
    return False
