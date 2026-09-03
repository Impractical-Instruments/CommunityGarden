{
    "patcher": {
        "fileversion": 1,
        "appversion": {
            "major": 9,
            "minor": 1,
            "revision": 5,
            "architecture": "x64",
            "modernui": 1
        },
        "classnamespace": "box",
        "rect": [ 171.0, 181.0, 524.0, 316.0 ],
        "boxes": [
            {
                "box": {
                    "id": "obj-8",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 32.0, 85.0, 29.5, 22.0 ],
                    "text": "0"
                }
            },
            {
                "box": {
                    "id": "obj-6",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 32.0, 32.0, 59.0, 22.0 ],
                    "text": "r initialize"
                }
            },
            {
                "box": {
                    "comment": "",
                    "id": "obj-5",
                    "index": 3,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "signal" ],
                    "patching_rect": [ 210.0, 81.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "",
                    "id": "obj-4",
                    "index": 2,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "signal" ],
                    "patching_rect": [ 158.0, 81.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "",
                    "id": "obj-3",
                    "index": 2,
                    "maxclass": "outlet",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 174.0, 460.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "",
                    "id": "obj-2",
                    "index": 1,
                    "maxclass": "outlet",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 102.0, 460.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "comment": "",
                    "id": "obj-1",
                    "index": 1,
                    "maxclass": "inlet",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 102.0, 81.0, 30.0, 30.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-16",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 229.0, 147.0, 128.0, 22.0 ],
                    "text": "prepend wet_dry_right"
                }
            },
            {
                "box": {
                    "id": "obj-14",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 102.0, 147.0, 121.0, 22.0 ],
                    "text": "prepend wet_dry_left"
                }
            },
            {
                "box": {
                    "autosave": 1,
                    "bgmode": 1,
                    "border": 0,
                    "clickthrough": 0,
                    "enablehscroll": 0,
                    "enablevscroll": 0,
                    "id": "obj-104",
                    "linecount": 3,
                    "lockeddragscroll": 0,
                    "lockedsize": 0,
                    "maxclass": "newobj",
                    "numinlets": 3,
                    "numoutlets": 4,
                    "offset": [ 0.0, 0.0 ],
                    "outlettype": [ "signal", "signal", "", "" ],
                    "patching_rect": [ 102.0, 201.0, 235.0, 196.0 ],
                    "presentation_linecount": 3,
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_invisible": 1,
                            "parameter_longname": "amxd~[108]",
                            "parameter_modmode": 0,
                            "parameter_shortname": "amxd~[12]",
                            "parameter_type": 3
                        }
                    },
                    "saved_object_attributes": {
                        "parameter_enable": 1,
                        "patchername": "Noyzckippr.amxd",
                        "patchername_fallback": "~/Projects/CommunityGarden/ShowControl/PlayingThePipes/Pipes Prototype 3/patchers/Noyzckippr.amxd"
                    },
                    "snapshot": {
                        "filetype": "C74Snapshot",
                        "version": 2,
                        "minorversion": 0,
                        "name": "snapshotlist",
                        "origin": "max~",
                        "type": "list",
                        "subtype": "Undefined",
                        "embed": 1,
                        "snapshot": {
                            "name": "Noyzckippr.amxd",
                            "origname": "~/Projects/CommunityGarden/ShowControl/PlayingThePipes/Pipes Prototype 3/patchers/Noyzckippr.amxd",
                            "valuedictionary": {
                                "parameter_values": {
                                    "link": 1.0,
                                    "noise_CF_L": 31.0,
                                    "noise_CF_R": 31.0,
                                    "noise_Q_L": 12.0,
                                    "noise_Q_R": 12.0,
                                    "noise_gainL": 0.57,
                                    "noise_gainR": 0.57,
                                    "noise_out_gain_L": 355.0,
                                    "noise_out_gain_R": 355.0,
                                    "wet_dry_left": 100.0,
                                    "wet_dry_right": 100.0
                                }
                            },
                            "active": 1
                        },
                        "snapshotlist": {
                            "current_snapshot": 0,
                            "entries": [
                                {
                                    "filetype": "C74Snapshot",
                                    "version": 2,
                                    "minorversion": 0,
                                    "name": "Noyzckippr.amxd",
                                    "origin": "Noyzckippr.amxd",
                                    "type": "amxd",
                                    "subtype": "Undefined",
                                    "embed": 1,
                                    "snapshot": {
                                        "name": "Noyzckippr.amxd",
                                        "origname": "~/Projects/CommunityGarden/ShowControl/PlayingThePipes/Pipes Prototype 3/patchers/Noyzckippr.amxd",
                                        "valuedictionary": {
                                            "parameter_values": {
                                                "link": 1.0,
                                                "noise_CF_L": 31.0,
                                                "noise_CF_R": 31.0,
                                                "noise_Q_L": 12.0,
                                                "noise_Q_R": 12.0,
                                                "noise_gainL": 0.57,
                                                "noise_gainR": 0.57,
                                                "noise_out_gain_L": 355.0,
                                                "noise_out_gain_R": 355.0,
                                                "wet_dry_left": 100.0,
                                                "wet_dry_right": 100.0
                                            }
                                        },
                                        "active": 1
                                    },
                                    "fileref": {
                                        "name": "Noyzckippr.amxd",
                                        "filename": "Noyzckippr.amxd_20260902.maxsnap",
                                        "filepath": "~/Projects/CommunityGarden/ShowControl/PlayingThePipes/Pipes Prototype 3/data",
                                        "filepos": -1,
                                        "snapshotfileid": "3c1a9d1926b5c66af906d97c15d0bd7c"
                                    }
                                }
                            ]
                        }
                    },
                    "text": "amxd~ \"Package:/Max for Live/patchers/Max Audio Effect/Noyzckippr/Noyzckippr.amxd\"",
                    "varname": "amxd~[12]",
                    "viewvisibility": 1
                }
            }
        ],
        "lines": [
            {
                "patchline": {
                    "destination": [ "obj-14", 0 ],
                    "order": 1,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-16", 0 ],
                    "order": 0,
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-2", 0 ],
                    "source": [ "obj-104", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-3", 0 ],
                    "source": [ "obj-104", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 0 ],
                    "source": [ "obj-14", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 0 ],
                    "source": [ "obj-16", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 0 ],
                    "source": [ "obj-4", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 1 ],
                    "source": [ "obj-5", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-14", 0 ],
                    "order": 1,
                    "source": [ "obj-8", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-16", 0 ],
                    "order": 0,
                    "source": [ "obj-8", 0 ]
                }
            }
        ]
    }
}