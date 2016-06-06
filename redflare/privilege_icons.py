import os


class IconNotFoundError(Exception):
    pass


def generate_privilege_icon(privilege_name, color):
    """
    Generates a colored version of a Red Eclipse privilege icon.

    :param str color: A color in the format #RGB or #RRGGBB
    :return: The colored privilege SVG icon
    :rtype: str
    """

    if len(color) not in (4, 7) or not color.startswith("#"):
        raise ValueError("Invalid color!")

    icon_dir = os.path.join(os.path.dirname(__file__), "privilege-icons")

    try:
        with open(os.path.join(icon_dir, privilege_name + ".svg")) as f:
            content = f.read()
    except IOError:
        raise IconNotFoundError()

    # order of white colors is important
    for white in ("#ffffff", "#fff"):
        content = content.replace(white, color)

    return content
