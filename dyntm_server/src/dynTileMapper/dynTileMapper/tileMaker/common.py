SPHEREMERC_GROUND_SIZE = (20037508.34*2)
# m --> map
MAPFILE = """
MAP
    NAME noname
    SIZE %(size)s
    SHAPEPATH "%(shapePath)s"
    EXTENT 0 0 1 1
    UNITS DD
    PROJECTION
        "init=epsg:3857"
    END
    IMAGECOLOR 0 0 0
    OUTPUTFORMAT
        NAME png 
        DRIVER "GD/PNG"
        TRANSPARENT ON
        MIMETYPE "image/png"
        IMAGEMODE RGB 
        EXTENSION "png" 
        FORMATOPTION "INTERLACE=[OFF]"
    END
    WEB
        METADATA
            "wms_sys" "EPSG:3857"
        END
    END
    LAYER
        NAME "tileme"
        TYPE POLYGON
        STATUS ON
        DATA "%(shapeName)s"
        PROJECTION
            "%(projString)s"
            #"init=epsg:4326"
            #"init=epsg:2223"
        END
        CLASS
            NAME 'dtm'
            STYLE
                OUTLINECOLOR 0 0 1
                COLOR %(color)s
            END
        END
    END
END
"""
