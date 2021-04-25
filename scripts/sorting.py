from datetime import datetime

def srname(object, reverse=False):
    objects = [(i[1].lower(), i) for i in object]
    objects.sort(key=lambda x: x[0])
    objects = [i[1] for i in objects]
    if reverse:
        objects = objects[::-1]
    return objects


def name(object, reverse=False):
    objects = [(i[0].lower(), i) for i in object]
    objects.sort(key=lambda x: x[0])
    objects = [i[1] for i in objects]
    if reverse:
        objects = objects[::-1]
    return objects


def date(object, reverse=False):
    objects = object.copy()
    try:
        dt_fmt ='%d.%m.%Y'
        objects = [(datetime.strptime(str(i[2]).lower(), dt_fmt), i) for i in object]
        objects.sort(key=lambda x: x[0])
        objects = [i[1] for i in objects]
        if reverse:
            objects = objects[::-1]
        return objects
    except Exception:
        return objects


def male(object, reverse=False, revers2=False):
    objects = [(i[3].lower(), i) for i in object]
    objects.sort(key=lambda x: 'ж' == x[0][0].lower())
    objects = [i[1] for i in objects]
    if reverse:
        objects = objects[::-1]
    if revers2:
        objects = objects[::-1]
    return objects


def female(object, reverse=False, revers2=True):
    objects = [(i[3].lower(), i) for i in object]
    objects.sort(key=lambda x: 'ж' == x[0][0].lower())
    objects = [i[1] for i in objects]
    if reverse:
        objects = objects[::-1]
    if revers2:
        objects = objects[::-1]
    return objects
