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
        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
        "boxes": [
            {
                "box": {
                    "id": "obj-142",
                    "lastchannelcount": 0,
                    "maxclass": "live.gain~",
                    "numinlets": 2,
                    "numoutlets": 5,
                    "outlettype": [ "signal", "signal", "", "float", "list" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 664.0000337362289, 1064.0, 48.0, 136.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_longname": "live.gain~[24]",
                            "parameter_mmax": 6.0,
                            "parameter_mmin": -70.0,
                            "parameter_modmode": 3,
                            "parameter_shortname": "live.gain~[24]",
                            "parameter_type": 0,
                            "parameter_unitstyle": 4
                        }
                    },
                    "varname": "live.gain~[1]"
                }
            },
            {
                "box": {
                    "id": "obj-85",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 925.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-86",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 851.0, 923.0, 36.0, 22.0 ],
                    "text": "r e12"
                }
            },
            {
                "box": {
                    "id": "obj-87",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 851.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-89",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 818.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-90",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 744.0, 923.0, 35.0, 22.0 ],
                    "text": "r e11"
                }
            },
            {
                "box": {
                    "id": "obj-91",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 744.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-92",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 712.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-93",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 638.0, 923.0, 36.0, 22.0 ],
                    "text": "r e10"
                }
            },
            {
                "box": {
                    "id": "obj-94",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 638.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-95",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 606.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-96",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 532.0, 923.0, 29.0, 22.0 ],
                    "text": "r e9"
                }
            },
            {
                "box": {
                    "id": "obj-97",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 532.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-100",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 499.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-101",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 425.0, 923.0, 29.0, 22.0 ],
                    "text": "r e8"
                }
            },
            {
                "box": {
                    "id": "obj-103",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 425.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-104",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 393.0, 987.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-105",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 319.0, 923.0, 29.0, 22.0 ],
                    "text": "r e7"
                }
            },
            {
                "box": {
                    "id": "obj-124",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 319.0, 956.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-82",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 876.6667228937149, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-83",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 802.6667228937149, 813.0, 29.0, 22.0 ],
                    "text": "r e6"
                }
            },
            {
                "box": {
                    "id": "obj-84",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 802.6667228937149, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-79",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 770.3333783149719, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-80",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 696.3333783149719, 813.0, 29.0, 22.0 ],
                    "text": "r e5"
                }
            },
            {
                "box": {
                    "id": "obj-81",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 696.3333783149719, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-76",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 664.0000337362289, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-77",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 590.0000337362289, 813.0, 29.0, 22.0 ],
                    "text": "r e4"
                }
            },
            {
                "box": {
                    "id": "obj-78",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 590.0000337362289, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-73",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 557.666689157486, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-74",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 483.66668915748596, 813.0, 29.0, 22.0 ],
                    "text": "r e3"
                }
            },
            {
                "box": {
                    "id": "obj-75",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 483.66668915748596, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-69",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 451.333344578743, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-70",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 377.333344578743, 813.0, 29.0, 22.0 ],
                    "text": "r e2"
                }
            },
            {
                "box": {
                    "id": "obj-72",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 377.333344578743, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-68",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 14,
                    "outlettype": [ "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal", "signal" ],
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "boxes": [
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-47",
                                    "index": 14,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1068.0, 445.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-46",
                                    "index": 13,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1023.0, 445.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 2,
                                    "numoutlets": 5,
                                    "outlettype": [ "signal", "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 1035.0, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[23]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "live.gain~[23]",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[22]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-43",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 963.0000000000002, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[21]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[20]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-44",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 876.5454545454547, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[22]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[21]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-33",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 790.0909090909092, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[11]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[10]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-34",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 703.6363636363637, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[12]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[11]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-35",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 617.1818181818182, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[13]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[12]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-36",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 530.7272727272727, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[14]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[13]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-37",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 444.27272727272725, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[15]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[14]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-38",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 357.8181818181818, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[16]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[15]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-39",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 271.3636363636364, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[17]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[16]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-40",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 184.9090909090909, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[18]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[17]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-41",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 98.45454545454545, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[19]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[18]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-42",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 12.0, 259.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[20]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[19]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-32",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 796.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[10]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[9]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-31",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 701.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[9]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[8]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-30",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 616.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[8]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[7]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-29",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 531.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[7]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[6]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-28",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 446.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[6]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[5]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-27",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 361.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[5]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[4]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-26",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 277.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[4]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[3]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-25",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 192.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[3]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[2]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-24",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 107.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[2]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~[1]"
                                }
                            },
                            {
                                "box": {
                                    "channels": 1,
                                    "id": "obj-23",
                                    "lastchannelcount": 0,
                                    "maxclass": "live.gain~",
                                    "numinlets": 1,
                                    "numoutlets": 4,
                                    "outlettype": [ "signal", "", "float", "list" ],
                                    "parameter_enable": 1,
                                    "patching_rect": [ 12.0, 51.0, 48.0, 136.0 ],
                                    "saved_attribute_attributes": {
                                        "valueof": {
                                            "parameter_longname": "live.gain~[1]",
                                            "parameter_mmax": 6.0,
                                            "parameter_mmin": -70.0,
                                            "parameter_modmode": 3,
                                            "parameter_shortname": "g",
                                            "parameter_type": 0,
                                            "parameter_unitstyle": 4
                                        }
                                    },
                                    "varname": "live.gain~"
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-22",
                                    "index": 12,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 374.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-21",
                                    "index": 11,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 342.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-20",
                                    "index": 10,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 310.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-19",
                                    "index": 9,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 278.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-18",
                                    "index": 8,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 246.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-17",
                                    "index": 7,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 214.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-16",
                                    "index": 6,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 182.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-15",
                                    "index": 5,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 150.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-14",
                                    "index": 4,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 118.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-13",
                                    "index": 3,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 86.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-12",
                                    "index": 2,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 54.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-11",
                                    "index": 1,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 22.0, 468.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 796.0, 16.0, 81.0, 22.0 ],
                                    "text": "r~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 701.0, 16.0, 79.0, 22.0 ],
                                    "text": "r~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 616.0, 16.0, 81.0, 22.0 ],
                                    "text": "r~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 531.0, 16.0, 79.0, 22.0 ],
                                    "text": "r~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 446.0, 16.0, 81.0, 22.0 ],
                                    "text": "r~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 361.0, 16.0, 79.0, 22.0 ],
                                    "text": "r~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 277.0, 16.0, 81.0, 22.0 ],
                                    "text": "r~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.0, 16.0, 79.0, 22.0 ],
                                    "text": "r~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 107.0, 16.0, 81.0, 22.0 ],
                                    "text": "r~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 12.0, 16.0, 79.0, 22.0 ],
                                    "text": "r~ Grain_1_L"
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-23", 0 ],
                                    "order": 1,
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 0 ],
                                    "order": 0,
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 1 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-24", 0 ],
                                    "order": 1,
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 1 ],
                                    "order": 0,
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "order": 0,
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "order": 1,
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "order": 0,
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "order": 1,
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "order": 1,
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-44", 0 ],
                                    "order": 0,
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "order": 1,
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-43", 0 ],
                                    "order": 0,
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "order": 1,
                                    "source": [ "obj-27", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-44", 0 ],
                                    "order": 0,
                                    "source": [ "obj-27", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "order": 1,
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-43", 0 ],
                                    "order": 0,
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-25", 0 ],
                                    "order": 1,
                                    "source": [ "obj-3", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 0 ],
                                    "order": 0,
                                    "source": [ "obj-3", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "order": 0,
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "order": 1,
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "order": 0,
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "order": 1,
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "source": [ "obj-33", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "source": [ "obj-35", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "source": [ "obj-37", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "source": [ "obj-39", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-26", 0 ],
                                    "order": 1,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 1 ],
                                    "order": 0,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-11", 0 ],
                                    "source": [ "obj-42", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "source": [ "obj-43", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "source": [ "obj-44", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-46", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "source": [ "obj-45", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "order": 1,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 0 ],
                                    "order": 0,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "order": 1,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 1 ],
                                    "order": 0,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "order": 1,
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 0 ],
                                    "order": 0,
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "order": 1,
                                    "source": [ "obj-8", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 1 ],
                                    "order": 0,
                                    "source": [ "obj-8", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-45", 0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ]
                    },
                    "patching_rect": [ 271.0, 771.0, 737.0, 22.0 ],
                    "text": "p GrainMix"
                }
            },
            {
                "box": {
                    "id": "obj-46",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 345.0, 877.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-49",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 271.0, 813.0, 29.0, 22.0 ],
                    "text": "r e1"
                }
            },
            {
                "box": {
                    "id": "obj-51",
                    "maxclass": "newobj",
                    "numinlets": 8,
                    "numoutlets": 2,
                    "outlettype": [ "multichannelsignal", "int" ],
                    "patching_rect": [ 271.0, 846.0, 92.5, 22.0 ],
                    "text": "autograin"
                }
            },
            {
                "box": {
                    "id": "obj-102",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "signal" ],
                    "patching_rect": [ 1205.6666731238365, 799.0, 81.0, 22.0 ],
                    "text": "r~ Grain_5_R"
                }
            },
            {
                "box": {
                    "id": "obj-11",
                    "lastchannelcount": 0,
                    "maxclass": "live.gain~",
                    "numinlets": 2,
                    "numoutlets": 5,
                    "outlettype": [ "signal", "signal", "", "float", "list" ],
                    "parameter_enable": 1,
                    "patching_rect": [ 524.0, 1069.0, 48.0, 136.0 ],
                    "saved_attribute_attributes": {
                        "valueof": {
                            "parameter_longname": "live.gain~",
                            "parameter_mmax": 6.0,
                            "parameter_mmin": -70.0,
                            "parameter_modmode": 3,
                            "parameter_shortname": "live.gain~",
                            "parameter_type": 0,
                            "parameter_unitstyle": 4
                        }
                    },
                    "varname": "live.gain~"
                }
            },
            {
                "box": {
                    "id": "obj-134",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 567.3333502411842, 382.00001138448715, 32.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 640.0, 539.0, 32.0, 20.0 ],
                    "text": "E12",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-137",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 477.3333475589752, 382.00001138448715, 29.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 534.0, 539.0, 31.0, 20.0 ],
                    "text": "E11",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-138",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 390.6666783094406, 382.00001138448715, 33.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 427.0, 539.0, 30.0, 20.0 ],
                    "text": "E10",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-139",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 301.3333423137665, 382.66667807102203, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 321.0, 539.0, 25.0, 20.0 ],
                    "text": "E9",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-140",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 213.3333396911621, 382.00001138448715, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 216.0, 539.0, 25.0, 20.0 ],
                    "text": "E8",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-141",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 123.3333370089531, 382.00001138448715, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 105.0, 539.0, 25.0, 20.0 ],
                    "text": "E7",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-133",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 515.3333486914635, 248.00000739097595, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 653.0, 362.0, 25.0, 20.0 ],
                    "text": "E6",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-132",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 425.33334600925446, 248.00000739097595, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 543.0, 362.0, 25.0, 20.0 ],
                    "text": "E5",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-131",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 338.66667675971985, 248.00000739097595, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 432.0, 362.0, 25.0, 20.0 ],
                    "text": "E4",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-129",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 249.33334076404572, 248.66667407751083, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 323.0, 362.0, 25.0, 20.0 ],
                    "text": "E3",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-127",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 161.33333814144135, 248.00000739097595, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 218.0, 362.0, 25.0, 20.0 ],
                    "text": "E2",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-125",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 71.33333545923233, 248.00000739097595, 25.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 103.0, 362.0, 25.0, 20.0 ],
                    "text": "E1",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-114",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 519.3333488106728, 380.6666780114174, 38.0, 22.0 ],
                    "text": "s e12"
                }
            },
            {
                "box": {
                    "id": "obj-116",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 431.3333461880684, 380.6666780114174, 37.0, 22.0 ],
                    "text": "s e11"
                }
            },
            {
                "box": {
                    "id": "obj-117",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 343.333343565464, 380.6666780114174, 38.0, 22.0 ],
                    "text": "s e10"
                }
            },
            {
                "box": {
                    "id": "obj-119",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 255.33334094285965, 380.6666780114174, 31.0, 22.0 ],
                    "text": "s e9"
                }
            },
            {
                "box": {
                    "id": "obj-120",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 167.33333832025528, 380.6666780114174, 31.0, 22.0 ],
                    "text": "s e8"
                }
            },
            {
                "box": {
                    "id": "obj-122",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 79.33333569765091, 380.6666780114174, 31.0, 22.0 ],
                    "text": "s e7"
                }
            },
            {
                "box": {
                    "id": "obj-113",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 469.33334732055664, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e6"
                }
            },
            {
                "box": {
                    "id": "obj-111",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 381.33334469795227, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e5"
                }
            },
            {
                "box": {
                    "id": "obj-110",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 293.3333420753479, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e4"
                }
            },
            {
                "box": {
                    "id": "obj-109",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 205.33333945274353, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e3"
                }
            },
            {
                "box": {
                    "id": "obj-108",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 117.33333683013916, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e2"
                }
            },
            {
                "box": {
                    "id": "obj-106",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 29.33333420753479, 246.6666740179062, 31.0, 22.0 ],
                    "text": "s e1"
                }
            },
            {
                "box": {
                    "id": "obj-57",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 4,
                    "outlettype": [ "signal", "signal", "list", "list" ],
                    "patching_rect": [ 524.0, 1216.0, 83.0, 22.0 ],
                    "text": "omx.peaklim~"
                }
            },
            {
                "box": {
                    "id": "obj-169",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 0,
                    "patching_rect": [ 524.0, 1260.0, 40.0, 22.0 ],
                    "text": "dac~"
                }
            },
            {
                "box": {
                    "id": "obj-2",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1151.3333676457405, 162.00000482797623, 61.0, 22.0 ],
                    "text": "s initialize"
                }
            },
            {
                "box": {
                    "id": "obj-5",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "patching_rect": [ 1151.3333676457405, 120.66667026281357, 58.0, 22.0 ],
                    "text": "loadbang"
                }
            },
            {
                "box": {
                    "id": "obj-7",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 976.6666957736015, 274.6666748523712, 95.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 966.0, 449.0, 95.0, 20.0 ],
                    "text": "30 second cycle",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-8",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 948.6666949391365, 320.66667622327805, 77.0, 22.0 ],
                    "text": "s MetroBang"
                }
            },
            {
                "box": {
                    "id": "obj-401",
                    "maxclass": "button",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 948.6666949391365, 272.0000081062317, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 1064.0, 447.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-399",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "patching_rect": [ 948.6666949391365, 226.66667342185974, 76.0, 22.0 ],
                    "text": "metro 30000"
                }
            },
            {
                "box": {
                    "id": "obj-143",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 1298.6667053699493, 58.0000017285347, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 1013.0, 358.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-9",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ -204.0, 214.0, 1434.0, 847.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "patching_rect": [ 66.9761905670166, 159.0, 57.0, 20.0 ],
                                    "text": "delay 2000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 13,
                                    "outlettype": [ "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang", "bang" ],
                                    "patching_rect": [ 67.0, 185.0, 717.0, 20.0 ],
                                    "text": "t b b b b b b b b b b b b b"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 66.9761905670166, 129.0, 46.0, 20.0 ],
                                    "text": "deferlow"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "patching_rect": [ 66.9761905670166, 100.0, 50.0, 20.0 ],
                                    "text": "loadbang"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-419",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 325.9761905670166, 448.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample8"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-420",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 323.9761905670166, 401.0, 111.0, 20.0 ],
                                    "text": "replace vfm.mouth.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-423",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 187.9761905670166, 448.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample7"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-424",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 185.9761905670166, 402.0, 124.0, 20.0 ],
                                    "text": "replace percRhythm1.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-160",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 333.9761905670166, 577.0, 109.0, 23.0 ],
                                    "text": "buffer~ sample13"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-161",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 333.9761905670166, 517.0, 100.0, 20.0 ],
                                    "text": "replace C.mdlr2.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-164",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 197.9761905670166, 577.0, 109.0, 23.0 ],
                                    "text": "buffer~ sample12"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-165",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 197.9761905670166, 518.0, 125.0, 20.0 ],
                                    "text": "replace casioVl1.beat.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-168",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 67.9761905670166, 577.0, 108.0, 23.0 ],
                                    "text": "buffer~ sample11"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-170",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 67.9761905670166, 518.0, 100.0, 20.0 ],
                                    "text": "replace G.mdlr2.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-173",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 581.9761905670166, 448.0, 109.0, 23.0 ],
                                    "text": "buffer~ sample10"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-174",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 579.9761905670166, 400.0, 137.0, 20.0 ],
                                    "text": "replace bass.ArpMagnet.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-177",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 455.9761905670166, 448.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample9"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-178",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 453.9761905670166, 401.0, 99.0, 20.0 ],
                                    "text": "replace KickHat.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 64.9761905670166, 448.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample6"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 62.9761905670166, 401.0, 110.0, 20.0 ],
                                    "text": "replace Mallet.vfm.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 616.9761905670166, 311.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 618.9761905670166, 259.0, 125.0, 20.0 ],
                                    "text": "replace shakerswings.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 478.9761905670166, 311.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 480.9761905670166, 259.0, 120.0, 20.0 ],
                                    "text": "replace percClacks1.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 312.9761905670166, 311.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample3"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 314.9761905670166, 259.0, 156.0, 20.0 ],
                                    "text": "replace steel.bowls.slow.ALT.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 187.9761905670166, 311.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 189.9761905670166, 259.0, 98.0, 20.0 ],
                                    "text": "replace tone.31.wav"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "float", "bang" ],
                                    "patching_rect": [ 68.9761905670166, 311.0, 102.0, 23.0 ],
                                    "text": "buffer~ sample1"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 68.9761905670166, 259.0, 98.0, 20.0 ],
                                    "text": "replace tone.50.wav"
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-11", 0 ],
                                    "midpoints": [ 324.4761905670166, 306.0, 322.4761905670166, 306.0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "midpoints": [ 192.83333333333331, 246.0, 324.4761905670166, 246.0 ],
                                    "source": [ "obj-13", 2 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "midpoints": [ 251.0, 246.0, 490.4761905670166, 246.0 ],
                                    "source": [ "obj-13", 3 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-161", 0 ],
                                    "midpoints": [ 774.5, 504.0, 343.4761905670166, 504.0 ],
                                    "source": [ "obj-13", 12 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-165", 0 ],
                                    "midpoints": [ 716.3333333333334, 246.0, 600.0, 246.0, 600.0, 387.0, 564.0, 387.0, 564.0, 435.0, 300.0, 435.0, 300.0, 504.0, 207.4761905670166, 504.0 ],
                                    "source": [ "obj-13", 11 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 76.5, 255.0, 78.4761905670166, 255.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-170", 0 ],
                                    "midpoints": [ 658.1666666666666, 246.0, 48.0, 246.0, 48.0, 504.0, 77.4761905670166, 504.0 ],
                                    "source": [ "obj-13", 10 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-174", 0 ],
                                    "midpoints": [ 600.0, 387.0, 589.4761905670166, 387.0 ],
                                    "source": [ "obj-13", 9 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-178", 0 ],
                                    "midpoints": [ 541.8333333333333, 246.0, 471.0, 246.0, 471.0, 297.0, 463.4761905670166, 297.0 ],
                                    "source": [ "obj-13", 8 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 134.66666666666666, 246.0, 199.4761905670166, 246.0 ],
                                    "source": [ "obj-13", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 309.16666666666663, 246.0, 628.4761905670166, 246.0 ],
                                    "source": [ "obj-13", 4 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-26", 0 ],
                                    "midpoints": [ 367.3333333333333, 246.0, 54.0, 246.0, 54.0, 387.0, 72.4761905670166, 387.0 ],
                                    "source": [ "obj-13", 5 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-420", 0 ],
                                    "midpoints": [ 483.6666666666667, 246.0, 471.0, 246.0, 471.0, 297.0, 426.0, 297.0, 426.0, 387.0, 333.4761905670166, 387.0 ],
                                    "source": [ "obj-13", 7 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-424", 0 ],
                                    "midpoints": [ 425.5, 246.0, 297.0, 246.0, 297.0, 387.0, 195.4761905670166, 387.0 ],
                                    "source": [ "obj-13", 6 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "midpoints": [ 490.4761905670166, 306.0, 488.4761905670166, 306.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-160", 0 ],
                                    "midpoints": [ 343.4761905670166, 540.0, 343.4761905670166, 540.0 ],
                                    "source": [ "obj-161", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-164", 0 ],
                                    "midpoints": [ 207.4761905670166, 540.0, 207.4761905670166, 540.0 ],
                                    "source": [ "obj-165", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "midpoints": [ 78.4761905670166, 282.0, 78.4761905670166, 282.0 ],
                                    "source": [ "obj-17", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-168", 0 ],
                                    "midpoints": [ 77.4761905670166, 540.0, 77.4761905670166, 540.0 ],
                                    "source": [ "obj-170", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-173", 0 ],
                                    "midpoints": [ 589.4761905670166, 444.0, 591.4761905670166, 444.0 ],
                                    "source": [ "obj-174", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-177", 0 ],
                                    "midpoints": [ 463.4761905670166, 444.0, 465.4761905670166, 444.0 ],
                                    "source": [ "obj-178", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "midpoints": [ 76.4761905670166, 180.0, 76.5, 180.0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 199.4761905670166, 306.0, 197.4761905670166, 306.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 628.4761905670166, 306.0, 626.4761905670166, 306.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-25", 0 ],
                                    "midpoints": [ 72.4761905670166, 423.0, 74.4761905670166, 423.0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-9", 0 ],
                                    "midpoints": [ 76.4761905670166, 123.0, 76.4761905670166, 123.0 ],
                                    "source": [ "obj-3", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-419", 0 ],
                                    "midpoints": [ 333.4761905670166, 423.0, 335.4761905670166, 423.0 ],
                                    "source": [ "obj-420", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-423", 0 ],
                                    "midpoints": [ 195.4761905670166, 423.0, 197.4761905670166, 423.0 ],
                                    "source": [ "obj-424", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "midpoints": [ 76.4761905670166, 150.0, 76.4761905670166, 150.0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 1362.666707277298, 274.00000816583633, 86.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p AudioBuffers"
                }
            },
            {
                "box": {
                    "id": "obj-279",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 693.3333539962769, 180.6666720509529, 35.0, 22.0 ],
                    "text": "clear"
                }
            },
            {
                "box": {
                    "id": "obj-308",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 655.3333528637886, 274.00000816583633, 73.0, 22.0 ],
                    "text": "r StartMusic"
                }
            },
            {
                "box": {
                    "id": "obj-307",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 3,
                    "outlettype": [ "", "int", "int" ],
                    "patching_rect": [ 748.666688978672, 274.00000816583633, 48.0, 22.0 ],
                    "text": "change"
                }
            },
            {
                "box": {
                    "id": "obj-269",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 749.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 749.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 966.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 637.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 859.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 84.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 319.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 192.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 423.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 423.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-40",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-41",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1069.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 533.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-47",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1069.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 205.0, 148.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 205.0, 102.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1067.75, 636.0, 33.0, 20.0 ],
                                    "text": "r~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 636.0, 32.0, 20.0 ],
                                    "text": "r~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 636.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 636.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 636.0, 39.0, 20.0 ],
                                    "text": "r~ 12R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 749.5, 636.0, 37.0, 20.0 ],
                                    "text": "r~ 12L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 636.0, 39.0, 20.0 ],
                                    "text": "r~ 10R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 636.0, 37.0, 20.0 ],
                                    "text": "r~ 10L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 423.5, 636.0, 39.0, 20.0 ],
                                    "text": "r~ 13R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 636.0, 37.0, 20.0 ],
                                    "text": "r~ 13L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 290.0, 102.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 290.0, 63.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 290.0, 148.0, 34.0, 20.0 ],
                                    "text": "== 12"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 290.0, 193.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 331.0, 352.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 290.0, 298.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 368.0, 298.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 290.0, 244.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 368.0, 244.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 331.0, 422.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "midpoints": [ 759.0, 730.0, 759.0, 730.0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 976.0, 730.0, 976.0, 730.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 647.0, 730.0, 647.0, 730.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 869.0, 730.0, 869.0, 730.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 94.0, 730.0, 94.0, 730.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 329.0, 730.0, 329.0, 730.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 202.0, 730.0, 202.0, 730.0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "midpoints": [ 433.0, 730.0, 433.0, 730.0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "midpoints": [ 543.0, 730.0, 543.0, 730.0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "midpoints": [ 1079.0, 730.0, 1079.0, 730.0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 1 ],
                                    "midpoints": [ 340.5, 621.0, 735.0, 621.0, 735.0, 696.0, 769.5, 696.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 1 ],
                                    "midpoints": [ 340.5, 621.0, 951.0, 621.0, 951.0, 696.0, 986.5, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 340.5, 621.0, 624.0, 621.0, 624.0, 696.0, 657.5, 696.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 340.5, 621.0, 846.0, 621.0, 846.0, 696.0, 879.5, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 340.5, 621.0, 126.0, 621.0, 126.0, 696.0, 104.5, 696.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 340.5, 621.0, 366.0, 621.0, 366.0, 696.0, 339.5, 696.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 1 ],
                                    "midpoints": [ 340.5, 621.0, 237.0, 621.0, 237.0, 696.0, 212.5, 696.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 1 ],
                                    "midpoints": [ 340.5, 621.0, 408.0, 621.0, 408.0, 696.0, 443.5, 696.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 1 ],
                                    "midpoints": [ 340.5, 621.0, 519.0, 621.0, 519.0, 696.0, 553.5, 696.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 1 ],
                                    "midpoints": [ 340.5, 621.0, 1053.0, 621.0, 1053.0, 696.0, 1089.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 1126.66670024395, 696.6666874289513, 60.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State12"
                }
            },
            {
                "box": {
                    "id": "obj-268",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 194.0, 171.0, 1493.0, 888.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 749.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 749.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 966.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 637.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 859.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 84.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 319.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 192.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 423.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 423.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-40",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-41",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1069.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 533.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-47",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1069.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 264.5, 127.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 264.5, 81.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1067.75, 626.0, 33.0, 20.0 ],
                                    "text": "r~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 626.0, 32.0, 20.0 ],
                                    "text": "r~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 626.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 626.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 626.0, 39.0, 20.0 ],
                                    "text": "r~ 12R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 749.5, 626.0, 37.0, 20.0 ],
                                    "text": "r~ 12L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 626.0, 39.0, 20.0 ],
                                    "text": "r~ 10R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 626.0, 37.0, 20.0 ],
                                    "text": "r~ 10L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 423.5, 626.0, 38.0, 20.0 ],
                                    "text": "r~ 11R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 626.0, 36.0, 20.0 ],
                                    "text": "r~ 11L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 361.5, 81.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 361.5, 42.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 361.5, 127.0, 33.0, 20.0 ],
                                    "text": "== 11"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 361.5, 172.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 402.5, 331.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 361.5, 277.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 439.5, 277.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 361.5, 229.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 439.5, 229.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 402.5, 401.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "midpoints": [ 759.0, 730.0, 759.0, 730.0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 976.0, 730.0, 976.0, 730.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 647.0, 730.0, 647.0, 730.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 869.0, 730.0, 869.0, 730.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 94.0, 730.0, 94.0, 730.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 329.0, 730.0, 329.0, 730.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 202.0, 730.0, 202.0, 730.0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "midpoints": [ 433.0, 730.0, 433.0, 730.0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "midpoints": [ 543.0, 730.0, 543.0, 730.0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "midpoints": [ 1079.0, 730.0, 1079.0, 730.0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 1 ],
                                    "midpoints": [ 412.0, 612.0, 735.0, 612.0, 735.0, 696.0, 769.5, 696.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 1 ],
                                    "midpoints": [ 412.0, 612.0, 951.0, 612.0, 951.0, 696.0, 986.5, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 412.0, 612.0, 624.0, 612.0, 624.0, 696.0, 657.5, 696.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 412.0, 612.0, 846.0, 612.0, 846.0, 696.0, 879.5, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 412.0, 612.0, 126.0, 612.0, 126.0, 696.0, 104.5, 696.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 412.0, 612.0, 366.0, 612.0, 366.0, 696.0, 339.5, 696.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 1 ],
                                    "midpoints": [ 412.0, 612.0, 237.0, 612.0, 237.0, 696.0, 212.5, 696.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 1 ],
                                    "midpoints": [ 412.0, 696.0, 443.5, 696.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 1 ],
                                    "midpoints": [ 412.0, 612.0, 519.0, 612.0, 519.0, 696.0, 553.5, 696.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 1 ],
                                    "midpoints": [ 412.0, 612.0, 1053.0, 612.0, 1053.0, 696.0, 1089.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 1034.6666975021362, 696.6666874289513, 59.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State11"
                }
            },
            {
                "box": {
                    "id": "obj-267",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 213.0, 115.0, 1264.0, 899.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 695.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 695.0, 760.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 912.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 912.0, 760.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 583.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 583.0, 760.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 805.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 805.0, 760.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 30.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 30.0, 760.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 265.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 265.0, 760.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 138.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 138.0, 760.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 369.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 369.0, 760.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-40",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 479.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-41",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1015.0, 697.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 479.0, 760.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-47",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1015.0, 760.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 271.5, 146.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 271.5, 100.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1015.0, 626.0, 33.0, 20.0 ],
                                    "text": "r~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 912.0, 626.0, 32.0, 20.0 ],
                                    "text": "r~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 138.0, 626.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 30.0, 626.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 805.0, 626.0, 33.0, 20.0 ],
                                    "text": "r~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 695.0, 626.0, 32.0, 20.0 ],
                                    "text": "r~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 583.0, 626.0, 39.0, 20.0 ],
                                    "text": "r~ 10R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 479.0, 626.0, 37.0, 20.0 ],
                                    "text": "r~ 10L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 369.0, 626.0, 38.0, 20.0 ],
                                    "text": "r~ 11R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 265.0, 626.0, 36.0, 20.0 ],
                                    "text": "r~ 11L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 360.5, 100.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 360.5, 61.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 360.5, 146.0, 34.0, 20.0 ],
                                    "text": "== 10"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 360.5, 191.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 401.5, 350.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 360.5, 296.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 438.5, 296.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 360.5, 245.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 438.5, 245.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 401.5, 420.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "midpoints": [ 704.5, 718.0, 704.5, 718.0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 921.5, 718.0, 921.5, 718.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 592.5, 718.0, 592.5, 718.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 814.5, 718.0, 814.5, 718.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 39.5, 718.0, 39.5, 718.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 274.5, 718.0, 274.5, 718.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 147.5, 718.0, 147.5, 718.0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "midpoints": [ 378.5, 718.0, 378.5, 718.0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "midpoints": [ 488.5, 718.0, 488.5, 718.0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "midpoints": [ 1024.5, 718.0, 1024.5, 718.0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 1 ],
                                    "midpoints": [ 411.0, 612.0, 681.0, 612.0, 681.0, 684.0, 715.0, 684.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 1 ],
                                    "midpoints": [ 411.0, 612.0, 897.0, 612.0, 897.0, 684.0, 932.0, 684.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 411.0, 612.0, 570.0, 612.0, 570.0, 684.0, 603.0, 684.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 411.0, 612.0, 792.0, 612.0, 792.0, 684.0, 825.0, 684.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 411.0, 612.0, 72.0, 612.0, 72.0, 684.0, 50.0, 684.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 411.0, 612.0, 312.0, 612.0, 312.0, 684.0, 285.0, 684.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 1 ],
                                    "midpoints": [ 411.0, 612.0, 183.0, 612.0, 183.0, 684.0, 158.0, 684.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 1 ],
                                    "midpoints": [ 411.0, 612.0, 417.0, 612.0, 417.0, 684.0, 389.0, 684.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 1 ],
                                    "midpoints": [ 411.0, 612.0, 465.0, 612.0, 465.0, 684.0, 499.0, 684.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 1 ],
                                    "midpoints": [ 411.0, 612.0, 1002.0, 612.0, 1002.0, 684.0, 1035.0, 684.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 938.6666946411133, 696.6666874289513, 60.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State10"
                }
            },
            {
                "box": {
                    "id": "obj-266",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 60.0, 112.0, 1634.0, 955.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 749.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 749.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 966.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 637.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 859.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 84.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 319.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 192.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 423.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 423.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-40",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-41",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1069.5, 709.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 533.5, 772.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-47",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1069.5, 772.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 288.5, 146.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 288.5, 100.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1069.5, 613.0, 33.0, 20.0 ],
                                    "text": "r~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 966.5, 613.0, 32.0, 20.0 ],
                                    "text": "r~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 192.5, 613.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 84.5, 613.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 859.5, 613.0, 33.0, 20.0 ],
                                    "text": "r~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 748.5, 613.0, 32.0, 20.0 ],
                                    "text": "r~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 637.5, 613.0, 39.0, 20.0 ],
                                    "text": "r~ 10R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 533.5, 613.0, 37.0, 20.0 ],
                                    "text": "r~ 10L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 426.5, 613.0, 33.0, 20.0 ],
                                    "text": "r~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 319.5, 613.0, 32.0, 20.0 ],
                                    "text": "r~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 385.5, 100.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 385.5, 61.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 385.5, 146.0, 29.5, 20.0 ],
                                    "text": "== 9"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 385.5, 191.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 426.5, 350.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 385.5, 296.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 463.5, 296.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 385.5, 246.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 463.5, 246.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 426.5, 428.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "midpoints": [ 759.0, 730.0, 759.0, 730.0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 976.0, 730.0, 976.0, 730.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 647.0, 730.0, 647.0, 730.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 869.0, 730.0, 869.0, 730.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 94.0, 730.0, 94.0, 730.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 329.0, 730.0, 329.0, 730.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 202.0, 730.0, 202.0, 730.0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "midpoints": [ 433.0, 730.0, 433.0, 730.0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "midpoints": [ 543.0, 730.0, 543.0, 730.0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "midpoints": [ 1079.0, 730.0, 1079.0, 730.0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 1 ],
                                    "midpoints": [ 436.0, 600.0, 735.0, 600.0, 735.0, 696.0, 769.5, 696.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 1 ],
                                    "midpoints": [ 436.0, 600.0, 951.0, 600.0, 951.0, 696.0, 986.5, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 436.0, 600.0, 624.0, 600.0, 624.0, 696.0, 657.5, 696.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 436.0, 600.0, 846.0, 600.0, 846.0, 696.0, 879.5, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 436.0, 600.0, 126.0, 600.0, 126.0, 696.0, 104.5, 696.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 436.0, 600.0, 363.0, 600.0, 363.0, 696.0, 339.5, 696.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 1 ],
                                    "midpoints": [ 436.0, 600.0, 237.0, 600.0, 237.0, 696.0, 212.5, 696.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 1 ],
                                    "midpoints": [ 436.0, 600.0, 411.0, 600.0, 411.0, 696.0, 443.5, 696.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 1 ],
                                    "midpoints": [ 436.0, 600.0, 519.0, 600.0, 519.0, 696.0, 553.5, 696.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 1 ],
                                    "midpoints": [ 436.0, 600.0, 1056.0, 600.0, 1056.0, 696.0, 1089.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 849.3333586454391, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State9"
                }
            },
            {
                "box": {
                    "id": "obj-259",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 134.0, 167.0, 1503.0, 889.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 697.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 697.25, 781.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 914.0, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 914.0, 781.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 585.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 585.25, 781.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 807.0, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 807.0, 781.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 32.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 32.25, 781.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 267.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 267.25, 781.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 140.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 140.25, 781.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 370.5, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 370.5, 781.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-40",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 481.0, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-41",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1017.25, 718.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 481.0, 781.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-47",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1017.25, 781.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 305.5, 120.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 305.5, 74.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1017.25, 619.0, 33.0, 20.0 ],
                                    "text": "r~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 914.0, 619.0, 32.0, 20.0 ],
                                    "text": "r~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 145.0, 619.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 32.25, 619.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 807.0, 619.0, 33.0, 20.0 ],
                                    "text": "r~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 697.25, 619.0, 32.0, 20.0 ],
                                    "text": "r~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 585.25, 619.0, 33.0, 20.0 ],
                                    "text": "r~ 8R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 481.0, 619.0, 32.0, 20.0 ],
                                    "text": "r~ 8L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 370.5, 619.0, 33.0, 20.0 ],
                                    "text": "r~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 267.25, 619.0, 32.0, 20.0 ],
                                    "text": "r~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 398.5, 74.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 398.5, 35.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 398.5, 120.0, 29.5, 20.0 ],
                                    "text": "== 8"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 398.5, 165.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 439.5, 324.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 398.5, 270.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 476.5, 270.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 398.5, 217.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 476.5, 217.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 439.5, 394.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 923.5, 739.0, 923.5, 739.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 594.75, 739.0, 594.75, 739.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 816.5, 739.0, 816.5, 739.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 41.75, 739.0, 41.75, 739.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 276.75, 739.0, 276.75, 739.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 149.75, 739.0, 149.75, 739.0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-39", 0 ],
                                    "midpoints": [ 380.0, 739.0, 380.0, 739.0 ],
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-42", 0 ],
                                    "midpoints": [ 490.5, 739.0, 490.5, 739.0 ],
                                    "source": [ "obj-40", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-47", 0 ],
                                    "midpoints": [ 1026.75, 739.0, 1026.75, 739.0 ],
                                    "source": [ "obj-41", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 449.0, 705.0, 934.0, 705.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 449.0, 705.0, 605.25, 705.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 449.0, 705.0, 827.0, 705.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 449.0, 705.0, 52.25, 705.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 449.0, 705.0, 287.25, 705.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 1 ],
                                    "midpoints": [ 449.0, 705.0, 160.25, 705.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-38", 1 ],
                                    "midpoints": [ 449.0, 705.0, 390.5, 705.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-40", 1 ],
                                    "midpoints": [ 449.0, 705.0, 501.0, 705.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 1 ],
                                    "midpoints": [ 449.0, 705.0, 1037.25, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 1 ],
                                    "midpoints": [ 449.0, 705.0, 717.25, 705.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 706.75, 739.0, 706.75, 739.0 ],
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-41", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 756.6666892170906, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State8"
                }
            },
            {
                "box": {
                    "id": "obj-258",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 319.0, 140.0, 1375.0, 932.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 737.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 737.0, 830.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 846.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 846.0, 830.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 625.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 625.0, 830.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 955.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 955.0, 830.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 72.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 72.0, 830.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 307.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 307.0, 830.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 180.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 180.0, 830.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 517.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 517.0, 830.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 409.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1057.0, 767.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 409.0, 830.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-37",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1057.0, 830.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-38",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 955.0, 648.0, 33.0, 20.0 ],
                                    "text": "r~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-39",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 737.0, 648.0, 32.0, 20.0 ],
                                    "text": "r~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-48",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 180.0, 648.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-49",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 72.0, 648.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 390.5, 139.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 390.5, 93.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 625.0, 648.0, 33.0, 20.0 ],
                                    "text": "r~ 8R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 517.0, 648.0, 32.0, 20.0 ],
                                    "text": "r~ 8L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 409.0, 648.0, 33.0, 20.0 ],
                                    "text": "r~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 307.0, 648.0, 32.0, 20.0 ],
                                    "text": "r~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 487.5, 93.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 487.5, 54.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 487.5, 139.0, 29.5, 20.0 ],
                                    "text": "== 7"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 487.5, 184.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 528.5, 343.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 487.5, 289.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 565.5, 289.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 487.5, 236.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 565.5, 236.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 528.5, 413.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "midpoints": [ 634.5, 788.0, 634.5, 788.0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 964.5, 788.0, 964.5, 788.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "midpoints": [ 81.5, 788.0, 81.5, 788.0 ],
                                    "source": [ "obj-15", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-9", 0 ],
                                    "midpoints": [ 855.5, 788.0, 855.5, 788.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 316.5, 788.0, 316.5, 788.0 ],
                                    "source": [ "obj-28", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 189.5, 788.0, 189.5, 788.0 ],
                                    "source": [ "obj-30", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 526.5, 788.0, 526.5, 788.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-36", 0 ],
                                    "midpoints": [ 418.5, 788.0, 418.5, 788.0 ],
                                    "source": [ "obj-34", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-37", 0 ],
                                    "midpoints": [ 1066.5, 788.0, 1066.5, 788.0 ],
                                    "source": [ "obj-35", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "midpoints": [ 964.5, 671.0, 964.5, 671.0 ],
                                    "order": 1,
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 0 ],
                                    "midpoints": [ 964.5, 731.69140625, 1066.5, 731.69140625 ],
                                    "order": 0,
                                    "source": [ "obj-38", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 746.5, 726.078125, 855.5, 726.078125 ],
                                    "order": 0,
                                    "source": [ "obj-39", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 0 ],
                                    "midpoints": [ 746.5, 671.0, 746.5, 671.0 ],
                                    "order": 1,
                                    "source": [ "obj-39", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-10", 0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-10", 1 ],
                                    "midpoints": [ 538.0, 633.0, 612.0, 633.0, 612.0, 753.0, 645.0, 753.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 538.0, 633.0, 942.0, 633.0, 942.0, 753.0, 975.0, 753.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 1 ],
                                    "midpoints": [ 538.0, 633.0, 114.0, 633.0, 114.0, 753.0, 92.0, 753.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 538.0, 633.0, 866.0, 633.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 1 ],
                                    "midpoints": [ 538.0, 633.0, 351.0, 633.0, 351.0, 753.0, 327.0, 753.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 1 ],
                                    "midpoints": [ 538.0, 633.0, 225.0, 633.0, 225.0, 753.0, 200.0, 753.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 538.0, 633.0, 561.0, 633.0, 561.0, 753.0, 537.0, 753.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 1 ],
                                    "midpoints": [ 538.0, 633.0, 453.0, 633.0, 453.0, 753.0, 429.0, 753.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-35", 1 ],
                                    "midpoints": [ 538.0, 633.0, 1077.0, 633.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 1 ],
                                    "midpoints": [ 538.0, 633.0, 723.0, 633.0, 723.0, 753.0, 757.0, 753.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-48", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "source": [ "obj-49", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 746.5, 788.0, 746.5, 788.0 ],
                                    "source": [ "obj-8", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 676.6666868329048, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State7"
                }
            },
            {
                "box": {
                    "id": "obj-254",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 134.0, 153.0, 1560.0, 930.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 659.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 659.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 735.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 735.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 844.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 844.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 624.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 624.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 953.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 953.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 91.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 91.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 306.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 199.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 199.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 516.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 408.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1055.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 408.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1055.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 953.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 735.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 569.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 358.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-23",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-24",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 199.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 91.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 359.6774219274521, 152.74193167686462, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 359.6774219274521, 106.77418941259384, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 452.41935807466507, 106.77418941259384, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 452.41935807466507, 67.2580600976944, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 452.41935807466507, 152.74193167686462, 29.5, 20.0 ],
                                    "text": "== 6"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 452.41935807466507, 197.09677070379257, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 493.54839062690735, 356.7741912007332, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 452.41935807466507, 302.74193274974823, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 530.6451650857925, 302.74193274974823, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 452.41935807466507, 250.80645340681076, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 530.6451650857925, 250.80645340681076, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 493.54839062690735, 426.12903040647507, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 744.5, 705.0, 853.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 0 ],
                                    "midpoints": [ 744.5, 624.0, 744.5, 624.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 315.5, 741.0, 315.5, 741.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "midpoints": [ 208.5, 741.0, 208.5, 741.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 578.5, 645.0, 525.5, 645.0 ],
                                    "source": [ "obj-15", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "midpoints": [ 367.5, 645.0, 315.5, 645.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 0 ],
                                    "midpoints": [ 100.5, 741.0, 100.5, 741.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 962.5, 741.0, 962.5, 741.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 853.5, 741.0, 853.5, 741.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 525.5, 624.0, 525.5, 624.0 ],
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "midpoints": [ 525.5, 741.0, 525.5, 741.0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 417.5, 741.0, 417.5, 741.0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "midpoints": [ 1064.5, 741.0, 1064.5, 741.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "source": [ "obj-35", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 633.5, 741.0, 633.5, 741.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 326.0, 705.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 219.0, 705.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 111.0, 705.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 973.0, 705.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 864.0, 705.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 536.0, 705.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 428.0, 705.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 1075.0, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 644.0, 705.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 1 ],
                                    "midpoints": [ 503.04839062690735, 705.0, 755.0, 705.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "order": 1,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 315.5, 705.0, 417.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "order": 1,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 525.5, 705.0, 633.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 744.5, 741.0, 744.5, 741.0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 962.5, 624.0, 962.5, 624.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 962.5, 705.0, 1064.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 589.3333508968353, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State6"
                }
            },
            {
                "box": {
                    "id": "obj-253",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 50.0, 145.0, 1644.0, 938.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 659.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 659.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 735.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 735.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 844.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 844.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 624.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 624.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 953.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 953.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 91.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 91.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 306.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 199.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 199.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 516.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 408.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1055.0, 720.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 408.0, 783.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1055.0, 783.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 953.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 4R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 735.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 4L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 569.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 358.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-23",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 516.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-24",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 306.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 199.0, 601.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 91.0, 601.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 293.0, 128.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 293.0, 82.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 387.0, 82.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 387.0, 43.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 387.0, 128.0, 29.5, 20.0 ],
                                    "text": "== 5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 387.0, 173.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 428.0, 332.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 387.0, 278.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 465.0, 278.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 387.0, 226.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 465.0, 226.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 428.0, 402.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 744.5, 705.0, 853.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 0 ],
                                    "midpoints": [ 744.5, 624.0, 744.5, 624.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 315.5, 741.0, 315.5, 741.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "midpoints": [ 208.5, 741.0, 208.5, 741.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 578.5, 645.0, 525.5, 645.0 ],
                                    "source": [ "obj-15", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "midpoints": [ 367.5, 645.0, 315.5, 645.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 0 ],
                                    "midpoints": [ 100.5, 741.0, 100.5, 741.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 962.5, 741.0, 962.5, 741.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 853.5, 741.0, 853.5, 741.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 525.5, 624.0, 525.5, 624.0 ],
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "midpoints": [ 525.5, 741.0, 525.5, 741.0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 417.5, 741.0, 417.5, 741.0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "midpoints": [ 1064.5, 741.0, 1064.5, 741.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "source": [ "obj-35", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 633.5, 741.0, 633.5, 741.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 437.5, 705.0, 326.0, 705.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 437.5, 705.0, 219.0, 705.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 437.5, 705.0, 111.0, 705.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 1 ],
                                    "midpoints": [ 437.5, 705.0, 973.0, 705.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 437.5, 705.0, 864.0, 705.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 437.5, 705.0, 536.0, 705.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 437.5, 705.0, 428.0, 705.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 437.5, 705.0, 1075.0, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 437.5, 705.0, 644.0, 705.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 1 ],
                                    "midpoints": [ 437.5, 705.0, 755.0, 705.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "order": 1,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 315.5, 705.0, 417.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "order": 1,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 525.5, 705.0, 633.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 744.5, 741.0, 744.5, 741.0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 962.5, 624.0, 962.5, 624.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 962.5, 705.0, 1064.5, 705.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 501.33334827423096, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State5"
                }
            },
            {
                "box": {
                    "id": "obj-239",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "visible": 1,
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-60",
                                    "maxclass": "comment",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 686.0, 261.0, 89.0, 18.0 ],
                                    "text": "Level starts at 1/2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 833.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 833.0, 705.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 942.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-23",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 942.0, 705.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-24",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1045.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1045.0, 705.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1142.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1142.0, 705.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 139.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 139.0, 705.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 248.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 248.0, 705.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 351.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 351.0, 705.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 448.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 448.0, 705.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 465.0, 110.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 624.0, 110.0, 29.5, 20.0 ],
                                    "text": "1"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 624.0, 64.0, 62.0, 20.0 ],
                                    "text": "r StartMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 465.0, 64.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 731.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 547.0, 642.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 731.0, 504.0, 33.0, 20.0 ],
                                    "text": "r~ 1R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 139.0, 504.0, 32.0, 20.0 ],
                                    "text": "r~ 1L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 731.0, 705.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 547.0, 705.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 553.0, 64.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 553.0, 25.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 553.0, 110.0, 29.5, 20.0 ],
                                    "text": "== 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 553.0, 171.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 594.0, 314.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 553.0, 260.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 631.0, 260.0, 53.0, 20.0 ],
                                    "text": "0.5 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 553.0, 217.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 631.0, 217.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 594.0, 384.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "midpoints": [ 148.5, 627.0, 360.5, 627.0 ],
                                    "order": 2,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "midpoints": [ 148.5, 627.0, 257.5, 627.0 ],
                                    "order": 3,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "midpoints": [ 148.5, 525.0, 148.5, 525.0 ],
                                    "order": 4,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 148.5, 627.0, 457.5, 627.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 0 ],
                                    "midpoints": [ 148.5, 627.0, 556.5, 627.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "midpoints": [ 474.5, 142.96484375, 562.5, 142.96484375 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-23", 0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-25", 0 ],
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "source": [ "obj-3", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "midpoints": [ 633.5, 145.62109375, 562.5, 145.62109375 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 603.5, 627.0, 371.0, 627.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 1 ],
                                    "midpoints": [ 603.5, 627.0, 268.0, 627.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 603.5, 627.0, 159.0, 627.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 1 ],
                                    "midpoints": [ 603.5, 627.0, 853.0, 627.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 603.5, 627.0, 962.0, 627.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-24", 1 ],
                                    "midpoints": [ 603.5, 627.0, 1065.0, 627.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-26", 1 ],
                                    "midpoints": [ 603.5, 627.0, 1162.0, 627.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 1 ],
                                    "midpoints": [ 603.5, 627.0, 468.0, 627.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 1 ],
                                    "midpoints": [ 603.5, 627.0, 751.0, 627.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 1 ],
                                    "midpoints": [ 603.5, 627.0, 567.0, 627.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "midpoints": [ 562.5, 203.6875, 640.5, 203.6875 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-8", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "midpoints": [ 740.5, 627.0, 842.5, 627.0 ],
                                    "order": 3,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 740.5, 627.0, 951.5, 627.0 ],
                                    "order": 2,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-24", 0 ],
                                    "midpoints": [ 740.5, 627.0, 1054.5, 627.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-26", 0 ],
                                    "midpoints": [ 740.5, 627.0, 1151.5, 627.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 0 ],
                                    "midpoints": [ 740.5, 525.0, 740.5, 525.0 ],
                                    "order": 4,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 69.33333539962769, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State0"
                }
            },
            {
                "box": {
                    "id": "obj-238",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 134.0, 167.0, 1560.0, 916.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 501.0, 644.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 291.0, 644.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 720.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 720.0, 768.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 829.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 829.0, 768.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 609.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 609.0, 768.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 938.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 938.0, 768.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 76.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-8",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 76.0, 768.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 291.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 291.0, 768.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 184.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 184.0, 768.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 501.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 501.0, 768.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 393.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1040.0, 705.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 393.0, 768.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1040.0, 768.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 938.0, 586.0, 33.0, 20.0 ],
                                    "text": "r~ 4R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 720.0, 586.0, 32.0, 20.0 ],
                                    "text": "r~ 4L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 554.0, 586.0, 33.0, 20.0 ],
                                    "text": "r~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 343.0, 586.0, 32.0, 20.0 ],
                                    "text": "r~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-23",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 501.0, 586.0, 33.0, 20.0 ],
                                    "text": "r~ 2R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-24",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 291.0, 586.0, 32.0, 20.0 ],
                                    "text": "r~ 2L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-35",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 184.0, 586.0, 33.0, 20.0 ],
                                    "text": "r~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-36",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 76.0, 586.0, 32.0, 20.0 ],
                                    "text": "r~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 371.5, 144.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 371.5, 98.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 463.5, 98.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 463.5, 59.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 463.5, 144.0, 29.5, 20.0 ],
                                    "text": "== 4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 463.5, 189.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 504.5, 348.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 463.5, 294.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 541.5, 294.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 463.5, 239.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 541.5, 239.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 505.0, 401.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 729.5, 690.0, 838.5, 690.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 0 ],
                                    "midpoints": [ 729.5, 609.0, 729.5, 609.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 300.5, 726.0, 300.5, 726.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "midpoints": [ 193.5, 726.0, 193.5, 726.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 563.5, 630.0, 510.5, 630.0 ],
                                    "source": [ "obj-15", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "midpoints": [ 352.5, 630.0, 300.5, 630.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-8", 0 ],
                                    "midpoints": [ 85.5, 726.0, 85.5, 726.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 947.5, 726.0, 947.5, 726.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 838.5, 726.0, 838.5, 726.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 510.5, 609.0, 510.5, 609.0 ],
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "midpoints": [ 510.5, 726.0, 510.5, 726.0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 402.5, 726.0, 402.5, 726.0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "midpoints": [ 1049.5, 726.0, 1049.5, 726.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "source": [ "obj-35", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "source": [ "obj-36", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 618.5, 726.0, 618.5, 726.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 514.5, 573.0, 387.0, 573.0, 387.0, 690.0, 311.0, 690.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 514.5, 573.0, 228.0, 573.0, 228.0, 690.0, 204.0, 690.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 514.5, 573.0, 120.0, 573.0, 120.0, 690.0, 96.0, 690.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 1 ],
                                    "midpoints": [ 514.5, 573.0, 924.0, 573.0, 924.0, 690.0, 958.0, 690.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 514.5, 573.0, 849.0, 573.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 514.5, 573.0, 486.0, 573.0, 486.0, 690.0, 521.0, 690.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 514.5, 573.0, 413.0, 573.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 514.5, 573.0, 1060.0, 573.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 514.5, 573.0, 629.0, 573.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 1 ],
                                    "midpoints": [ 514.5, 573.0, 705.0, 573.0, 705.0, 690.0, 740.0, 690.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "order": 1,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 300.5, 690.0, 402.5, 690.0 ],
                                    "order": 0,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "order": 1,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 510.5, 690.0, 618.5, 690.0 ],
                                    "order": 0,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 729.5, 726.0, 729.5, 726.0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 947.5, 609.0, 947.5, 609.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 947.5, 690.0, 1049.5, 690.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 417.3333457708359, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State4"
                }
            },
            {
                "box": {
                    "id": "obj-237",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 281.0, 97.0, 1413.0, 948.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 461.5, 650.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 251.0, 650.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 680.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 680.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 789.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 789.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 569.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 569.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 898.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 898.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 36.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 36.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 251.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 251.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 144.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 144.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 461.5, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 461.5, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 353.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 1000.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 353.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 1000.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 377.5, 121.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 377.5, 75.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 898.0, 592.0, 33.0, 20.0 ],
                                    "text": "r~ 4R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 680.0, 592.0, 32.0, 20.0 ],
                                    "text": "r~ 4L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 514.5, 592.0, 33.0, 20.0 ],
                                    "text": "r~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 303.0, 592.0, 32.0, 20.0 ],
                                    "text": "r~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 461.5, 592.0, 33.0, 20.0 ],
                                    "text": "r~ 2R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 251.0, 592.0, 32.0, 20.0 ],
                                    "text": "r~ 2L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 144.0, 592.0, 33.0, 20.0 ],
                                    "text": "r~ 1R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 36.0, 592.0, 32.0, 20.0 ],
                                    "text": "r~ 1L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 461.5, 75.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 461.5, 36.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 461.5, 121.0, 29.5, 20.0 ],
                                    "text": "== 3"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 461.5, 166.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 502.5, 336.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 461.5, 282.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 539.5, 282.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 461.5, 222.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 539.5, 222.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 502.5, 395.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 907.5, 615.0, 907.5, 615.0 ],
                                    "order": 1,
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 907.5, 696.0, 1009.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "midpoints": [ 689.5, 615.0, 689.5, 615.0 ],
                                    "order": 1,
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 689.5, 696.0, 798.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 260.5, 732.0, 260.5, 732.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "midpoints": [ 153.5, 732.0, 153.5, 732.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "midpoints": [ 45.5, 732.0, 45.5, 732.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 907.5, 732.0, 907.5, 732.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 689.5, 732.0, 689.5, 732.0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 798.5, 732.0, 798.5, 732.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 471.0, 615.0, 471.0, 615.0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "midpoints": [ 471.0, 732.0, 471.0, 732.0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 362.5, 732.0, 362.5, 732.0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "midpoints": [ 1009.5, 732.0, 1009.5, 732.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 578.5, 732.0, 578.5, 732.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 524.0, 636.0, 471.0, 636.0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "midpoints": [ 312.5, 636.0, 260.5, 636.0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 512.0, 579.0, 345.0, 579.0, 345.0, 696.0, 271.0, 696.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 512.0, 579.0, 189.0, 579.0, 189.0, 696.0, 164.0, 696.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 512.0, 579.0, 78.0, 579.0, 78.0, 696.0, 56.0, 696.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 1 ],
                                    "midpoints": [ 512.0, 579.0, 885.0, 579.0, 885.0, 696.0, 918.0, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 1 ],
                                    "midpoints": [ 512.0, 579.0, 666.0, 579.0, 666.0, 696.0, 700.0, 696.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 512.0, 579.0, 809.0, 579.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 512.0, 696.0, 481.5, 696.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 512.0, 579.0, 373.0, 579.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 512.0, 579.0, 1020.0, 579.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 512.0, 579.0, 589.0, 579.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "order": 1,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 260.5, 696.0, 362.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-5", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "order": 1,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 471.0, 696.0, 578.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 329.3333431482315, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State3"
                }
            },
            {
                "box": {
                    "id": "obj-233",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 893.0, 653.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 638.0, 653.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 584.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 584.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 693.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 693.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 796.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 796.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 893.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 893.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 59.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 59.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 168.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 168.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 271.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 271.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 368.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 368.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 482.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 995.0, 711.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 482.0, 774.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 995.0, 774.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 427.0, 160.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 427.0, 114.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-45",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 893.0, 597.0, 33.0, 20.0 ],
                                    "text": "r~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-46",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 692.0, 597.0, 32.0, 20.0 ],
                                    "text": "r~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 796.0, 597.0, 33.0, 20.0 ],
                                    "text": "r~ 2R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 638.0, 597.0, 32.0, 20.0 ],
                                    "text": "r~ 2L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 271.0, 597.0, 33.0, 20.0 ],
                                    "text": "r~ 1R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 168.0, 597.0, 32.0, 20.0 ],
                                    "text": "r~ 1L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 501.0, 114.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 501.0, 75.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 501.0, 160.0, 29.5, 20.0 ],
                                    "text": "== 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 501.0, 205.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 542.0, 364.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 501.0, 310.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 579.0, 310.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 501.0, 258.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 579.0, 258.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 542.0, 434.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "midpoints": [ 647.5, 696.0, 593.5, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 647.5, 696.0, 702.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 647.5, 696.0, 491.5, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "midpoints": [ 177.5, 660.0, 177.5, 660.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "midpoints": [ 177.5, 696.0, 68.5, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "midpoints": [ 902.5, 732.0, 902.5, 732.0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 177.5, 732.0, 177.5, 732.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "midpoints": [ 280.5, 732.0, 280.5, 732.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "midpoints": [ 68.5, 732.0, 68.5, 732.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "midpoints": [ 902.5, 675.0, 902.5, 675.0 ],
                                    "order": 1,
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 902.5, 696.0, 1004.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 902.5, 696.0, 805.5, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 593.5, 732.0, 593.5, 732.0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 702.5, 732.0, 702.5, 732.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 805.5, 639.0, 902.5, 639.0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 647.5, 618.0, 647.5, 618.0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "midpoints": [ 377.5, 732.0, 377.5, 732.0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "midpoints": [ 491.5, 732.0, 491.5, 732.0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "midpoints": [ 1004.5, 732.0, 1004.5, 732.0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-11", 0 ],
                                    "midpoints": [ 805.5, 732.0, 805.5, 732.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 902.5, 618.0, 902.5, 618.0 ],
                                    "source": [ "obj-45", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "midpoints": [ 701.5, 639.0, 647.5, 639.0 ],
                                    "source": [ "obj-46", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 1 ],
                                    "midpoints": [ 551.5, 696.0, 913.0, 696.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 551.5, 696.0, 188.0, 696.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 551.5, 696.0, 291.0, 696.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 551.5, 696.0, 79.0, 696.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 1 ],
                                    "midpoints": [ 551.5, 696.0, 604.0, 696.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 551.5, 696.0, 713.0, 696.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 551.5, 696.0, 388.0, 696.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 551.5, 696.0, 502.0, 696.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 551.5, 696.0, 1015.0, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 551.5, 696.0, 816.0, 696.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "midpoints": [ 280.5, 660.0, 280.5, 660.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 280.5, 696.0, 377.5, 696.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 241.33334052562714, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State2"
                }
            },
            {
                "box": {
                    "id": "obj-603",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 495.5, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 458.5, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-23",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 647.0, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-24",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 607.5, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 723.0, 574.0, 35.0, 20.0 ],
                                    "text": "*~ 0.2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 682.0, 574.0, 35.0, 20.0 ],
                                    "text": "*~ 0.2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 357.0, 713.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 317.0, 713.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 563.0, 574.0, 35.0, 20.0 ],
                                    "text": "*~ 0.3"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 521.0, 574.0, 35.0, 20.0 ],
                                    "text": "*~ 0.3"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-15",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 334.5, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-16",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 297.0, 434.0, 35.0, 20.0 ],
                                    "text": "*~ 0.5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 723.0, 265.0, 35.0, 20.0 ],
                                    "text": "*~ 1.2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 685.0, 265.0, 35.0, 20.0 ],
                                    "text": "*~ 1.2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 632.5, 109.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 595.0, 109.0, 35.0, 20.0 ],
                                    "text": "*~ 0.4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 409.0, 266.0, 29.5, 20.0 ],
                                    "text": "*~ 3."
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 371.0, 266.0, 29.5, 20.0 ],
                                    "text": "*~ 3."
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 297.0, 109.0, 29.5, 20.0 ],
                                    "text": "*~ 2."
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 334.5, 109.0, 29.5, 20.0 ],
                                    "text": "*~ 2."
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "patching_rect": [ 72.0, 153.0, 63.0, 20.0 ],
                                    "text": "delay 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 357.0, 760.0, 40.0, 20.0 ],
                                    "text": "s~ 13R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-5",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 317.0, 760.0, 39.0, 20.0 ],
                                    "text": "s~ 13L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 317.0, 672.0, 99.0, 20.0 ],
                                    "text": "groove~ sample13 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-117",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 178.0, 64.0, 62.0, 20.0 ],
                                    "text": "r StartMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-116",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 72.0, 64.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-326",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 723.0, 622.0, 40.0, 20.0 ],
                                    "text": "s~ 12R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-327",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 682.0, 622.0, 39.0, 20.0 ],
                                    "text": "s~ 12L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-328",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 647.5, 479.0, 40.0, 20.0 ],
                                    "text": "s~ 11R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-329",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 607.5, 479.0, 38.0, 20.0 ],
                                    "text": "s~ 11L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-330",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 563.0, 622.0, 40.0, 20.0 ],
                                    "text": "s~ 10R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-331",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 521.0, 622.0, 39.0, 20.0 ],
                                    "text": "s~ 10L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-332",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 495.5, 479.0, 35.0, 20.0 ],
                                    "text": "s~ 9R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-333",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 458.5, 479.0, 33.0, 20.0 ],
                                    "text": "s~ 9L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-334",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 404.0, 622.0, 35.0, 20.0 ],
                                    "text": "s~ 8R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-335",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 366.0, 622.0, 33.0, 20.0 ],
                                    "text": "s~ 8L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-336",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 334.5, 479.0, 35.0, 20.0 ],
                                    "text": "s~ 7R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-337",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 297.0, 479.0, 33.0, 20.0 ],
                                    "text": "s~ 7L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-322",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 723.0, 313.0, 35.0, 20.0 ],
                                    "text": "s~ 6R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-323",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 685.0, 313.0, 33.0, 20.0 ],
                                    "text": "s~ 6L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-324",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 632.5, 153.0, 35.0, 20.0 ],
                                    "text": "s~ 5R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-325",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 596.0, 153.0, 33.0, 20.0 ],
                                    "text": "s~ 5L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-318",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 562.0, 313.0, 35.0, 20.0 ],
                                    "text": "s~ 4R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-319",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 525.0, 313.0, 33.0, 20.0 ],
                                    "text": "s~ 4L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-320",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 488.0, 153.0, 35.0, 20.0 ],
                                    "text": "s~ 3R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-321",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 450.5, 153.0, 33.0, 20.0 ],
                                    "text": "s~ 3L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-316",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 409.0, 313.0, 35.0, 20.0 ],
                                    "text": "s~ 2R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-317",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 371.0, 313.0, 33.0, 20.0 ],
                                    "text": "s~ 2L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-314",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 334.5, 153.0, 35.0, 20.0 ],
                                    "text": "s~ 1R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-313",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 297.0, 153.0, 33.0, 20.0 ],
                                    "text": "s~ 1L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-307",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 521.5, 531.0, 99.0, 20.0 ],
                                    "text": "groove~ sample10 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-308",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 297.0, 386.0, 94.0, 20.0 ],
                                    "text": "groove~ sample7 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-309",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 682.5, 531.0, 99.0, 20.0 ],
                                    "text": "groove~ sample12 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-310",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 607.0, 386.0, 99.0, 20.0 ],
                                    "text": "groove~ sample11 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-311",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 458.5, 386.0, 94.0, 20.0 ],
                                    "text": "groove~ sample9 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-312",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 366.0, 531.0, 94.0, 20.0 ],
                                    "text": "groove~ sample8 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-132",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 524.0, 220.0, 94.0, 20.0 ],
                                    "text": "groove~ sample4 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-129",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 297.0, 64.0, 94.0, 20.0 ],
                                    "text": "groove~ sample1 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-133",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 72.0, 236.0, 29.5, 20.0 ],
                                    "text": "stop"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-80",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 224.0, 234.0, 29.5, 23.0 ],
                                    "text": "1"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-4",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 119.0, 234.0, 46.0, 23.0 ],
                                    "text": "loop 1"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-62",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 224.0, 297.0, 35.0, 23.0 ],
                                    "text": "sig~"
                                }
                            },
                            {
                                "box": {
                                    "fontname": "Arial",
                                    "fontsize": 13.0,
                                    "id": "obj-78",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 178.0, 234.0, 32.5, 23.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-122",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 685.0, 220.0, 94.0, 20.0 ],
                                    "text": "groove~ sample6 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-109",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 595.0, 57.0, 94.0, 20.0 ],
                                    "text": "groove~ sample5 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-77",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 451.0, 64.0, 94.0, 20.0 ],
                                    "text": "groove~ sample3 2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-61",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 3,
                                    "outlettype": [ "signal", "signal", "signal" ],
                                    "patching_rect": [ 371.0, 220.0, 94.0, 20.0 ],
                                    "text": "groove~ sample2 2"
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-133", 0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-316", 0 ],
                                    "midpoints": [ 418.5, 288.0, 418.5, 288.0 ],
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-11", 0 ],
                                    "midpoints": [ 604.5, 78.0, 604.5, 78.0 ],
                                    "source": [ "obj-109", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "midpoints": [ 642.0, 78.0, 642.0, 78.0 ],
                                    "source": [ "obj-109", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-325", 0 ],
                                    "midpoints": [ 604.5, 132.0, 605.5, 132.0 ],
                                    "source": [ "obj-11", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-116", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 187.5, 197.375, 128.5, 197.375 ],
                                    "order": 2,
                                    "source": [ "obj-117", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-78", 0 ],
                                    "midpoints": [ 187.5, 216.0, 187.5, 216.0 ],
                                    "order": 1,
                                    "source": [ "obj-117", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-80", 0 ],
                                    "midpoints": [ 187.5, 138.3359375, 233.5, 138.3359375 ],
                                    "order": 0,
                                    "source": [ "obj-117", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-324", 0 ],
                                    "midpoints": [ 642.0, 132.0, 642.0, 132.0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "midpoints": [ 732.0, 243.0, 732.5, 243.0 ],
                                    "source": [ "obj-122", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "midpoints": [ 694.5, 243.0, 694.5, 243.0 ],
                                    "source": [ "obj-122", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "midpoints": [ 344.0, 87.0, 344.0, 87.0 ],
                                    "source": [ "obj-129", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-7", 0 ],
                                    "midpoints": [ 306.5, 87.0, 306.5, 87.0 ],
                                    "source": [ "obj-129", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-322", 0 ],
                                    "midpoints": [ 732.5, 288.0, 732.5, 288.0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-318", 0 ],
                                    "midpoints": [ 571.0, 243.0, 571.5, 243.0 ],
                                    "source": [ "obj-132", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-319", 0 ],
                                    "midpoints": [ 533.5, 309.0, 534.5, 309.0 ],
                                    "source": [ "obj-132", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-109", 0 ],
                                    "midpoints": [ 81.5, 267.0, 282.0, 267.0, 282.0, 96.0, 582.0, 96.0, 582.0, 54.0, 604.5, 54.0 ],
                                    "order": 3,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-122", 0 ],
                                    "midpoints": [ 81.5, 267.0, 357.0, 267.0, 357.0, 252.0, 672.0, 252.0, 672.0, 216.0, 694.5, 216.0 ],
                                    "order": 0,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-129", 0 ],
                                    "midpoints": [ 81.5, 267.0, 282.0, 267.0, 282.0, 60.0, 306.5, 60.0 ],
                                    "order": 12,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-132", 0 ],
                                    "midpoints": [ 81.5, 267.0, 357.0, 267.0, 357.0, 252.0, 510.0, 252.0, 510.0, 216.0, 533.5, 216.0 ],
                                    "order": 4,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-307", 0 ],
                                    "midpoints": [ 81.5, 516.0, 531.0, 516.0 ],
                                    "order": 5,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-308", 0 ],
                                    "midpoints": [ 81.5, 372.0, 306.5, 372.0 ],
                                    "order": 11,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-309", 0 ],
                                    "midpoints": [ 81.5, 516.0, 692.0, 516.0 ],
                                    "order": 1,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-310", 0 ],
                                    "midpoints": [ 81.5, 372.0, 616.5, 372.0 ],
                                    "order": 2,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-311", 0 ],
                                    "midpoints": [ 81.5, 372.0, 468.0, 372.0 ],
                                    "order": 6,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-312", 0 ],
                                    "midpoints": [ 81.5, 516.0, 375.5, 516.0 ],
                                    "order": 9,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 81.5, 657.0, 326.5, 657.0 ],
                                    "order": 10,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-61", 0 ],
                                    "midpoints": [ 81.5, 267.0, 357.0, 267.0, 357.0, 216.0, 380.5, 216.0 ],
                                    "order": 8,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-77", 0 ],
                                    "midpoints": [ 81.5, 267.0, 282.0, 267.0, 282.0, 96.0, 438.0, 96.0, 438.0, 60.0, 460.5, 60.0 ],
                                    "order": 7,
                                    "source": [ "obj-133", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-323", 0 ],
                                    "midpoints": [ 694.5, 288.0, 694.5, 288.0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-336", 0 ],
                                    "midpoints": [ 344.0, 456.0, 344.0, 456.0 ],
                                    "source": [ "obj-15", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-337", 0 ],
                                    "midpoints": [ 306.5, 456.0, 306.5, 456.0 ],
                                    "source": [ "obj-16", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-330", 0 ],
                                    "midpoints": [ 572.5, 597.0, 572.5, 597.0 ],
                                    "source": [ "obj-17", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-331", 0 ],
                                    "midpoints": [ 530.5, 597.0, 530.5, 597.0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "midpoints": [ 366.5, 735.0, 366.5, 735.0 ],
                                    "source": [ "obj-19", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-314", 0 ],
                                    "midpoints": [ 344.0, 132.0, 344.0, 132.0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-5", 0 ],
                                    "midpoints": [ 326.5, 735.0, 326.5, 735.0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-326", 0 ],
                                    "midpoints": [ 732.5, 597.0, 732.5, 597.0 ],
                                    "source": [ "obj-21", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-327", 0 ],
                                    "midpoints": [ 691.5, 597.0, 691.5, 597.0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-328", 0 ],
                                    "midpoints": [ 656.5, 474.0, 657.0, 474.0 ],
                                    "source": [ "obj-23", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-329", 0 ],
                                    "midpoints": [ 617.0, 456.0, 617.0, 456.0 ],
                                    "source": [ "obj-24", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-332", 0 ],
                                    "midpoints": [ 505.0, 456.0, 505.0, 456.0 ],
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-333", 0 ],
                                    "midpoints": [ 468.0, 456.0, 468.0, 456.0 ],
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "midpoints": [ 571.0, 552.0, 572.5, 552.0 ],
                                    "source": [ "obj-307", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "midpoints": [ 531.0, 570.0, 530.5, 570.0 ],
                                    "source": [ "obj-307", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-15", 0 ],
                                    "source": [ "obj-308", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-16", 0 ],
                                    "midpoints": [ 306.5, 408.0, 306.5, 408.0 ],
                                    "source": [ "obj-308", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "midpoints": [ 732.0, 552.0, 732.5, 552.0 ],
                                    "source": [ "obj-309", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 692.0, 552.0, 691.5, 552.0 ],
                                    "source": [ "obj-309", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-23", 0 ],
                                    "midpoints": [ 656.5, 408.0, 656.5, 408.0 ],
                                    "source": [ "obj-310", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-24", 0 ],
                                    "midpoints": [ 616.5, 408.0, 617.0, 408.0 ],
                                    "source": [ "obj-310", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-25", 0 ],
                                    "midpoints": [ 505.5, 408.0, 505.0, 408.0 ],
                                    "source": [ "obj-311", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-26", 0 ],
                                    "midpoints": [ 468.0, 408.0, 468.0, 408.0 ],
                                    "source": [ "obj-311", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-334", 0 ],
                                    "midpoints": [ 413.0, 552.0, 413.5, 552.0 ],
                                    "source": [ "obj-312", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-335", 0 ],
                                    "midpoints": [ 375.5, 552.0, 375.5, 552.0 ],
                                    "source": [ "obj-312", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-109", 0 ],
                                    "midpoints": [ 128.5, 267.0, 282.0, 267.0, 282.0, 96.0, 582.0, 96.0, 582.0, 54.0, 604.5, 54.0 ],
                                    "order": 3,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-122", 0 ],
                                    "midpoints": [ 128.5, 267.0, 357.0, 267.0, 357.0, 252.0, 672.0, 252.0, 672.0, 216.0, 694.5, 216.0 ],
                                    "order": 0,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-129", 0 ],
                                    "midpoints": [ 128.5, 267.0, 282.0, 267.0, 282.0, 60.0, 306.5, 60.0 ],
                                    "order": 12,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-132", 0 ],
                                    "midpoints": [ 128.5, 267.0, 357.0, 267.0, 357.0, 252.0, 510.0, 252.0, 510.0, 216.0, 533.5, 216.0 ],
                                    "order": 4,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-307", 0 ],
                                    "midpoints": [ 128.5, 516.0, 531.0, 516.0 ],
                                    "order": 5,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-308", 0 ],
                                    "midpoints": [ 128.5, 372.0, 306.5, 372.0 ],
                                    "order": 11,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-309", 0 ],
                                    "midpoints": [ 128.5, 516.0, 692.0, 516.0 ],
                                    "order": 1,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-310", 0 ],
                                    "midpoints": [ 128.5, 372.0, 616.5, 372.0 ],
                                    "order": 2,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-311", 0 ],
                                    "midpoints": [ 128.5, 372.0, 468.0, 372.0 ],
                                    "order": 6,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-312", 0 ],
                                    "midpoints": [ 128.5, 516.0, 375.5, 516.0 ],
                                    "order": 9,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 128.5, 657.0, 326.5, 657.0 ],
                                    "order": 10,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-61", 0 ],
                                    "midpoints": [ 128.5, 267.0, 357.0, 267.0, 357.0, 216.0, 380.5, 216.0 ],
                                    "order": 8,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-77", 0 ],
                                    "midpoints": [ 128.5, 267.0, 282.0, 267.0, 282.0, 96.0, 438.0, 96.0, 438.0, 60.0, 460.5, 60.0 ],
                                    "order": 7,
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "midpoints": [ 366.5, 693.0, 366.5, 693.0 ],
                                    "source": [ "obj-6", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "midpoints": [ 326.5, 693.0, 326.5, 693.0 ],
                                    "source": [ "obj-6", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-10", 0 ],
                                    "midpoints": [ 418.0, 243.0, 418.5, 243.0 ],
                                    "source": [ "obj-61", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-9", 0 ],
                                    "midpoints": [ 380.5, 243.0, 380.5, 243.0 ],
                                    "source": [ "obj-61", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-109", 0 ],
                                    "midpoints": [ 233.5, 348.0, 282.0, 348.0, 282.0, 96.0, 582.0, 96.0, 582.0, 54.0, 604.5, 54.0 ],
                                    "order": 3,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-122", 0 ],
                                    "midpoints": [ 233.5, 348.0, 672.0, 348.0, 672.0, 216.0, 694.5, 216.0 ],
                                    "order": 0,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-129", 0 ],
                                    "midpoints": [ 233.5, 348.0, 282.0, 348.0, 282.0, 60.0, 306.5, 60.0 ],
                                    "order": 12,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-132", 0 ],
                                    "midpoints": [ 233.5, 348.0, 510.0, 348.0, 510.0, 216.0, 533.5, 216.0 ],
                                    "order": 4,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-307", 0 ],
                                    "midpoints": [ 233.5, 516.0, 531.0, 516.0 ],
                                    "order": 5,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-308", 0 ],
                                    "midpoints": [ 233.5, 372.0, 306.5, 372.0 ],
                                    "order": 11,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-309", 0 ],
                                    "midpoints": [ 233.5, 516.0, 692.0, 516.0 ],
                                    "order": 1,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-310", 0 ],
                                    "midpoints": [ 233.5, 372.0, 616.5, 372.0 ],
                                    "order": 2,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-311", 0 ],
                                    "midpoints": [ 233.5, 372.0, 468.0, 372.0 ],
                                    "order": 6,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-312", 0 ],
                                    "midpoints": [ 233.5, 516.0, 375.5, 516.0 ],
                                    "order": 9,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 233.5, 657.0, 326.5, 657.0 ],
                                    "order": 10,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-61", 0 ],
                                    "midpoints": [ 233.5, 348.0, 357.0, 348.0, 357.0, 216.0, 380.5, 216.0 ],
                                    "order": 8,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-77", 0 ],
                                    "midpoints": [ 233.5, 348.0, 282.0, 348.0, 282.0, 96.0, 438.0, 96.0, 438.0, 60.0, 460.5, 60.0 ],
                                    "order": 7,
                                    "source": [ "obj-62", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-313", 0 ],
                                    "midpoints": [ 306.5, 132.0, 306.5, 132.0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-320", 0 ],
                                    "midpoints": [ 498.0, 150.0, 497.5, 150.0 ],
                                    "source": [ "obj-77", 1 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-321", 0 ],
                                    "midpoints": [ 460.5, 87.0, 460.0, 87.0 ],
                                    "source": [ "obj-77", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-109", 0 ],
                                    "midpoints": [ 187.5, 267.0, 282.0, 267.0, 282.0, 96.0, 582.0, 96.0, 582.0, 54.0, 604.5, 54.0 ],
                                    "order": 3,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-122", 0 ],
                                    "midpoints": [ 187.5, 267.0, 357.0, 267.0, 357.0, 252.0, 672.0, 252.0, 672.0, 216.0, 694.5, 216.0 ],
                                    "order": 0,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-129", 0 ],
                                    "midpoints": [ 187.5, 267.0, 282.0, 267.0, 282.0, 60.0, 306.5, 60.0 ],
                                    "order": 12,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-132", 0 ],
                                    "midpoints": [ 187.5, 267.0, 357.0, 267.0, 357.0, 252.0, 510.0, 252.0, 510.0, 216.0, 533.5, 216.0 ],
                                    "order": 4,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-307", 0 ],
                                    "midpoints": [ 187.5, 516.0, 531.0, 516.0 ],
                                    "order": 5,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-308", 0 ],
                                    "midpoints": [ 187.5, 372.0, 306.5, 372.0 ],
                                    "order": 11,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-309", 0 ],
                                    "midpoints": [ 187.5, 516.0, 692.0, 516.0 ],
                                    "order": 1,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-310", 0 ],
                                    "midpoints": [ 187.5, 372.0, 616.5, 372.0 ],
                                    "order": 2,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-311", 0 ],
                                    "midpoints": [ 187.5, 372.0, 468.0, 372.0 ],
                                    "order": 6,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-312", 0 ],
                                    "midpoints": [ 187.5, 516.0, 375.5, 516.0 ],
                                    "order": 9,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "midpoints": [ 187.5, 657.0, 326.5, 657.0 ],
                                    "order": 10,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-61", 0 ],
                                    "midpoints": [ 187.5, 267.0, 357.0, 267.0, 357.0, 216.0, 380.5, 216.0 ],
                                    "order": 8,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-77", 0 ],
                                    "midpoints": [ 187.5, 267.0, 282.0, 267.0, 282.0, 96.0, 438.0, 96.0, 438.0, 60.0, 460.5, 60.0 ],
                                    "order": 7,
                                    "source": [ "obj-78", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-62", 0 ],
                                    "midpoints": [ 233.5, 258.0, 233.5, 258.0 ],
                                    "source": [ "obj-80", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-317", 0 ],
                                    "midpoints": [ 380.5, 288.0, 380.5, 288.0 ],
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 1363.3333739638329, 318.0000094771385, 83.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p MusicLoops"
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-597",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 1108.666699707508, 588.6666842103004, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 1136.0, 174.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample13",
                    "id": "obj-589",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 1108.666699707508, 622.0000185370445, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 1136.0, 207.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-579",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 0,
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
                        "rect": [ 34.0, 90.0, 1213.0, 549.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-20",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 561.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-21",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 561.0, 819.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_4_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-22",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 670.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 670.0, 819.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_5_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 773.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-11",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 773.0, 819.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_3_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-12",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 870.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-27",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 870.0, 819.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_4_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-18",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 36.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-19",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 36.0, 819.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_1_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-13",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 145.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-17",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 145.0, 819.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_2_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-14",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 248.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-28",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 248.0, 819.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_1_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-29",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 345.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-30",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 345.0, 819.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_2_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-31",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 459.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-32",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 972.0, 756.0, 29.5, 20.0 ],
                                    "text": "*~"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-33",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 459.0, 819.0, 69.0, 20.0 ],
                                    "text": "s~ Grain_3_L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-34",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 972.0, 819.0, 70.0, 20.0 ],
                                    "text": "s~ Grain_5_R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-55",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 196.0, 133.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-53",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 196.0, 87.0, 61.0, 20.0 ],
                                    "text": "r StopMusic"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-25",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 868.25, 641.0, 33.0, 20.0 ],
                                    "text": "r~ 2R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-26",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 559.75, 641.0, 32.0, 20.0 ],
                                    "text": "r~ 2L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-9",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 301.0, 641.0, 33.0, 20.0 ],
                                    "text": "r~ 1R"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-10",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "signal" ],
                                    "patching_rect": [ 88.0, 641.0, 32.0, 20.0 ],
                                    "text": "r~ 1L"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-498",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 275.0, 87.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-499",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 275.0, 48.0, 57.0, 20.0 ],
                                    "text": "r stateNum"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-500",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "patching_rect": [ 275.0, 133.0, 29.5, 20.0 ],
                                    "text": "== 1"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-501",
                                    "maxclass": "toggle",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "int" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 275.0, 178.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-472",
                                    "maxclass": "newobj",
                                    "numinlets": 3,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "patching_rect": [ 316.0, 337.0, 40.0, 20.0 ],
                                    "text": "line"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-473",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 275.0, 283.0, 47.0, 20.0 ],
                                    "text": "0. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-474",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 353.0, 283.0, 47.0, 20.0 ],
                                    "text": "1. 10000"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-475",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 275.0, 222.0, 30.0, 20.0 ],
                                    "text": "sel 0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-476",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "" ],
                                    "patching_rect": [ 353.0, 222.0, 30.0, 20.0 ],
                                    "text": "sel 1"
                                }
                            },
                            {
                                "box": {
                                    "floatoutput": 1,
                                    "id": "obj-470",
                                    "maxclass": "slider",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 316.0, 407.0, 20.0, 140.0 ],
                                    "size": 1.0
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 0 ],
                                    "midpoints": [ 97.5, 741.0, 154.5, 741.0 ],
                                    "order": 0,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 0 ],
                                    "midpoints": [ 97.5, 741.0, 45.5, 741.0 ],
                                    "order": 1,
                                    "source": [ "obj-10", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-27", 0 ],
                                    "source": [ "obj-12", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-17", 0 ],
                                    "source": [ "obj-13", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-28", 0 ],
                                    "source": [ "obj-14", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-19", 0 ],
                                    "source": [ "obj-18", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-21", 0 ],
                                    "source": [ "obj-20", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-3", 0 ],
                                    "source": [ "obj-22", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 0 ],
                                    "midpoints": [ 877.75, 741.0, 879.5, 741.0 ],
                                    "order": 1,
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 0 ],
                                    "midpoints": [ 877.75, 741.0, 981.5, 741.0 ],
                                    "order": 0,
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "midpoints": [ 877.75, 741.0, 782.5, 741.0 ],
                                    "order": 2,
                                    "source": [ "obj-25", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 0 ],
                                    "midpoints": [ 569.25, 741.0, 570.5, 741.0 ],
                                    "order": 1,
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 0 ],
                                    "midpoints": [ 569.25, 741.0, 679.5, 741.0 ],
                                    "order": 0,
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 0 ],
                                    "midpoints": [ 569.25, 741.0, 468.5, 741.0 ],
                                    "order": 2,
                                    "source": [ "obj-26", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-30", 0 ],
                                    "source": [ "obj-29", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-33", 0 ],
                                    "source": [ "obj-31", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-34", 0 ],
                                    "source": [ "obj-32", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-11", 0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-12", 1 ],
                                    "midpoints": [ 325.5, 627.0, 855.0, 627.0, 855.0, 741.0, 890.0, 741.0 ],
                                    "order": 1,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-13", 1 ],
                                    "midpoints": [ 325.5, 627.0, 165.0, 627.0 ],
                                    "order": 8,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 1 ],
                                    "midpoints": [ 325.5, 627.0, 268.0, 627.0 ],
                                    "order": 7,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-18", 1 ],
                                    "midpoints": [ 325.5, 627.0, 56.0, 627.0 ],
                                    "order": 9,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-20", 1 ],
                                    "midpoints": [ 325.5, 627.0, 546.0, 627.0, 546.0, 741.0, 581.0, 741.0 ],
                                    "order": 4,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-22", 1 ],
                                    "midpoints": [ 325.5, 627.0, 690.0, 627.0 ],
                                    "order": 3,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 1 ],
                                    "midpoints": [ 325.5, 627.0, 365.0, 627.0 ],
                                    "order": 6,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-31", 1 ],
                                    "midpoints": [ 325.5, 627.0, 479.0, 627.0 ],
                                    "order": 5,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-32", 1 ],
                                    "midpoints": [ 325.5, 627.0, 992.0, 627.0 ],
                                    "order": 0,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 1 ],
                                    "midpoints": [ 325.5, 627.0, 793.0, 627.0 ],
                                    "order": 2,
                                    "source": [ "obj-470", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-470", 0 ],
                                    "source": [ "obj-472", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-473", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-472", 0 ],
                                    "source": [ "obj-474", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-473", 0 ],
                                    "source": [ "obj-475", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-474", 0 ],
                                    "source": [ "obj-476", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-500", 0 ],
                                    "source": [ "obj-498", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-498", 0 ],
                                    "source": [ "obj-499", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-500", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-475", 0 ],
                                    "order": 1,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-476", 0 ],
                                    "order": 0,
                                    "source": [ "obj-501", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-55", 0 ],
                                    "source": [ "obj-53", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-501", 0 ],
                                    "source": [ "obj-55", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-14", 0 ],
                                    "midpoints": [ 310.5, 741.0, 257.5, 741.0 ],
                                    "order": 1,
                                    "source": [ "obj-9", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-29", 0 ],
                                    "midpoints": [ 310.5, 741.0, 354.5, 741.0 ],
                                    "order": 0,
                                    "source": [ "obj-9", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 153.33333790302277, 696.6666874289513, 53.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p State1"
                }
            },
            {
                "box": {
                    "id": "obj-492",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 748.666688978672, 362.0000107884407, 69.0, 22.0 ],
                    "text": "s stateNum"
                }
            },
            {
                "box": {
                    "id": "obj-422",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 216.66667312383652, 560.6666833758354, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 244.0, 146.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 8\nvfm.mouth.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-426",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 32.6666676402092, 562.0000167489052, 105.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 60.0, 147.0, 105.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 7 percRhythm1.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-213",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 1298.6667053699493, 116.0000034570694, 34.0, 22.0 ],
                    "text": "sel 0"
                }
            },
            {
                "box": {
                    "id": "obj-211",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "" ],
                    "patching_rect": [ 1376.6667076945305, 116.0000034570694, 34.0, 22.0 ],
                    "text": "sel 1"
                }
            },
            {
                "box": {
                    "buffername": "sample12",
                    "id": "obj-230",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 922.6666941642761, 622.0000185370445, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 950.0, 207.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample11",
                    "id": "obj-232",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 741.3333554267883, 622.0000185370445, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 769.0, 207.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample10",
                    "id": "obj-234",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 555.3333498835564, 624.0000185966492, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 583.0, 209.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample9",
                    "id": "obj-236",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 377.333344578743, 624.0000185966492, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 405.0, 209.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample8",
                    "id": "obj-222",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 190.66667234897614, 624.0000185966492, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 218.0, 209.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-223",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 190.66667234897614, 594.0000177025795, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 218.0, 179.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample7",
                    "id": "obj-224",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 6.000000178813934, 622.6666852235794, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 34.0, 208.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-225",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 6.000000178813934, 592.6666843295097, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 34.0, 178.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample6",
                    "id": "obj-226",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 918.6666940450668, 496.6666814684868, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 950.0, 94.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample5",
                    "id": "obj-220",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 738.6666886806488, 496.6666814684868, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 770.0, 94.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample4",
                    "id": "obj-194",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 555.3333498835564, 496.6666814684868, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 587.0, 94.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-207",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 555.3333498835564, 470.6666806936264, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 587.0, 68.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample3",
                    "id": "obj-208",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 373.3333444595337, 500.0000149011612, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 405.0, 97.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-209",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 373.3333444595337, 470.0000140070915, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 405.0, 67.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample2",
                    "id": "obj-136",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 186.66667222976685, 500.0000149011612, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 218.0, 97.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-154",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 186.66667222976685, 470.0000140070915, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 218.0, 67.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "buffername": "sample1",
                    "id": "obj-128",
                    "maxclass": "waveform~",
                    "numinlets": 5,
                    "numoutlets": 6,
                    "outlettype": [ "float", "float", "float", "float", "list", "" ],
                    "patching_rect": [ 9.333333611488342, 496.6666814684868, 150.0, 32.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 41.0, 94.0, 150.0, 32.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-99",
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 712.6666879057884, 322.6666762828827, 37.0, 20.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 964.0, 499.0, 37.0, 20.0 ],
                    "text": "State",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-126",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 948.6666949391365, 116.66667014360428, 29.5, 22.0 ],
                    "text": "1"
                }
            },
            {
                "box": {
                    "id": "obj-107",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 863.3333590626717, 116.66667014360428, 29.5, 22.0 ],
                    "text": "0"
                }
            },
            {
                "box": {
                    "id": "obj-71",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 748.666688978672, 322.0000095963478, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 1000.0, 498.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-58",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 748.666688978672, 228.0000067949295, 48.0, 22.0 ],
                    "text": "pipe 50"
                }
            },
            {
                "box": {
                    "id": "obj-181",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 748.666688978672, 180.6666720509529, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-121",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 863.3333590626717, 66.00000196695328, 72.0, 22.0 ],
                    "text": "r StopMusic"
                }
            },
            {
                "box": {
                    "id": "obj-118",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 948.6666949391365, 66.00000196695328, 73.0, 22.0 ],
                    "text": "r StartMusic"
                }
            },
            {
                "box": {
                    "id": "obj-115",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1298.6667053699493, 156.66667133569717, 74.0, 22.0 ],
                    "text": "s StopMusic"
                }
            },
            {
                "box": {
                    "id": "obj-112",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1376.6667076945305, 156.66667133569717, 75.0, 22.0 ],
                    "text": "s StartMusic"
                }
            },
            {
                "box": {
                    "id": "obj-98",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 948.6666949391365, 176.00000524520874, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-88",
                    "maxclass": "newobj",
                    "numinlets": 0,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
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
                        "rect": [ 147.0, 169.0, 1173.0, 780.0 ],
                        "default_fontsize": 10.0,
                        "subpatcher_template": "audiostart",
                        "boxes": [
                            {
                                "box": {
                                    "id": "obj-7",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "patching_rect": [ 837.0, 257.0, 50.0, 20.0 ],
                                    "text": "loadbang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-6",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 923.0, 360.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "comment": "",
                                    "id": "obj-213",
                                    "index": 1,
                                    "maxclass": "outlet",
                                    "numinlets": 1,
                                    "numoutlets": 0,
                                    "patching_rect": [ 889.0, 652.0, 30.0, 30.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-212",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 889.0, 597.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-210",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 805.0, 552.0, 66.0, 20.0 ],
                                    "text": "value Ecount"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-209",
                                    "maxclass": "newobj",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 889.0, 552.0, 47.0, 20.0 ],
                                    "text": "v Ecount"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-203",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "patching_rect": [ 837.0, 362.0, 41.0, 20.0 ],
                                    "text": "delay 1"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-200",
                                    "maxclass": "number",
                                    "numinlets": 1,
                                    "numoutlets": 2,
                                    "outlettype": [ "", "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 805.0, 496.0, 50.0, 20.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-192",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 889.0, 302.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-183",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 731.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-184",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 703.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-185",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 703.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-186",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 703.0, 257.0, 31.0, 20.0 ],
                                    "text": "r e12"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-187",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 703.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-155",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 210.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-156",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 182.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-157",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 182.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-158",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 182.0, 257.0, 26.0, 20.0 ],
                                    "text": "r e7"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-159",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 182.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-160",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 312.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-161",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 284.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-162",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 284.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-163",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 284.0, 257.0, 26.0, 20.0 ],
                                    "text": "r e8"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-164",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 284.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-165",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 414.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-166",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 386.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-167",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 386.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-168",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 386.0, 257.0, 26.0, 20.0 ],
                                    "text": "r e9"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-169",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 386.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-170",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 518.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-171",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 490.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-172",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 490.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-173",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 490.0, 257.0, 31.0, 20.0 ],
                                    "text": "r e10"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-174",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 490.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-175",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 624.0, 304.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-176",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 596.0, 302.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-177",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 596.0, 348.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-178",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 596.0, 257.0, 31.0, 20.0 ],
                                    "text": "r e11"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-179",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 596.0, 382.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-150",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 278.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-151",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 250.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-152",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 250.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-153",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 250.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e1"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-154",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 250.0, 190.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-145",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 380.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-146",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 352.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-147",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 352.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-148",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 352.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e2"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-149",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 352.0, 190.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-140",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 482.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-141",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 454.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-142",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 454.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-143",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 454.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e3"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-144",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 454.0, 190.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-135",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 586.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-136",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 558.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-137",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 558.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-138",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 558.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e4"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-139",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 558.0, 190.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-43",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 692.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-42",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 796.0, 112.0, 64.0, 20.0 ],
                                    "text": "r MetroBang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-1",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 664.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-2",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 664.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-3",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 664.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e5"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-4",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 664.0, 190.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-85",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 768.0, 110.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-81",
                                    "maxclass": "newobj",
                                    "numinlets": 2,
                                    "numoutlets": 2,
                                    "outlettype": [ "bang", "bang" ],
                                    "patching_rect": [ 768.0, 156.0, 47.0, 20.0 ],
                                    "text": "onebang"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-58",
                                    "maxclass": "newobj",
                                    "numinlets": 0,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 768.0, 65.0, 26.0, 20.0 ],
                                    "text": "r e6"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-410",
                                    "maxclass": "button",
                                    "numinlets": 1,
                                    "numoutlets": 1,
                                    "outlettype": [ "bang" ],
                                    "parameter_enable": 0,
                                    "patching_rect": [ 805.0, 199.0, 24.0, 24.0 ]
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-406",
                                    "maxclass": "message",
                                    "numinlets": 2,
                                    "numoutlets": 1,
                                    "outlettype": [ "" ],
                                    "patching_rect": [ 837.0, 408.0, 29.5, 20.0 ],
                                    "text": "0"
                                }
                            },
                            {
                                "box": {
                                    "id": "obj-404",
                                    "maxclass": "newobj",
                                    "numinlets": 5,
                                    "numoutlets": 4,
                                    "outlettype": [ "int", "", "", "int" ],
                                    "patching_rect": [ 805.0, 449.0, 61.0, 20.0 ],
                                    "text": "counter"
                                }
                            }
                        ],
                        "lines": [
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 0 ],
                                    "source": [ "obj-1", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-137", 1 ],
                                    "source": [ "obj-135", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-137", 0 ],
                                    "source": [ "obj-136", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-139", 0 ],
                                    "source": [ "obj-137", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-136", 0 ],
                                    "source": [ "obj-138", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 567.5, 238.0, 814.5, 238.0 ],
                                    "source": [ "obj-139", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-142", 1 ],
                                    "source": [ "obj-140", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-142", 0 ],
                                    "source": [ "obj-141", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-144", 0 ],
                                    "source": [ "obj-142", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-141", 0 ],
                                    "source": [ "obj-143", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 463.5, 238.0, 814.5, 238.0 ],
                                    "source": [ "obj-144", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-147", 1 ],
                                    "source": [ "obj-145", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-147", 0 ],
                                    "source": [ "obj-146", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-149", 0 ],
                                    "source": [ "obj-147", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-146", 0 ],
                                    "source": [ "obj-148", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 361.5, 238.0, 814.5, 238.0 ],
                                    "source": [ "obj-149", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-152", 1 ],
                                    "source": [ "obj-150", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-152", 0 ],
                                    "source": [ "obj-151", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-154", 0 ],
                                    "source": [ "obj-152", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-151", 0 ],
                                    "source": [ "obj-153", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 259.5, 238.0, 814.5, 238.0 ],
                                    "source": [ "obj-154", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-157", 1 ],
                                    "source": [ "obj-155", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-157", 0 ],
                                    "source": [ "obj-156", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-159", 0 ],
                                    "source": [ "obj-157", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-156", 0 ],
                                    "source": [ "obj-158", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 191.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-159", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-162", 1 ],
                                    "source": [ "obj-160", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-162", 0 ],
                                    "source": [ "obj-161", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-164", 0 ],
                                    "source": [ "obj-162", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-161", 0 ],
                                    "source": [ "obj-163", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 293.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-164", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-167", 1 ],
                                    "source": [ "obj-165", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-167", 0 ],
                                    "source": [ "obj-166", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-169", 0 ],
                                    "source": [ "obj-167", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-166", 0 ],
                                    "source": [ "obj-168", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 395.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-169", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-172", 1 ],
                                    "source": [ "obj-170", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-172", 0 ],
                                    "source": [ "obj-171", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-174", 0 ],
                                    "source": [ "obj-172", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-171", 0 ],
                                    "source": [ "obj-173", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 499.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-174", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-177", 1 ],
                                    "source": [ "obj-175", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-177", 0 ],
                                    "source": [ "obj-176", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-179", 0 ],
                                    "source": [ "obj-177", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-176", 0 ],
                                    "source": [ "obj-178", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 605.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-179", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-185", 1 ],
                                    "source": [ "obj-183", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-185", 0 ],
                                    "source": [ "obj-184", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-187", 0 ],
                                    "source": [ "obj-185", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-184", 0 ],
                                    "source": [ "obj-186", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 712.5, 436.0, 814.5, 436.0 ],
                                    "source": [ "obj-187", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-203", 0 ],
                                    "order": 2,
                                    "source": [ "obj-192", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-209", 0 ],
                                    "order": 1,
                                    "source": [ "obj-192", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-6", 0 ],
                                    "order": 0,
                                    "source": [ "obj-192", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-4", 0 ],
                                    "source": [ "obj-2", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-210", 0 ],
                                    "source": [ "obj-200", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-406", 0 ],
                                    "source": [ "obj-203", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-212", 0 ],
                                    "source": [ "obj-209", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-213", 0 ],
                                    "source": [ "obj-212", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-1", 0 ],
                                    "source": [ "obj-3", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "midpoints": [ 673.5, 238.0, 814.5, 238.0 ],
                                    "source": [ "obj-4", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-200", 0 ],
                                    "source": [ "obj-404", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 3 ],
                                    "source": [ "obj-406", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-404", 0 ],
                                    "source": [ "obj-410", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-81", 1 ],
                                    "source": [ "obj-42", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-2", 1 ],
                                    "source": [ "obj-43", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-85", 0 ],
                                    "source": [ "obj-58", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-406", 0 ],
                                    "source": [ "obj-7", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-410", 0 ],
                                    "source": [ "obj-81", 0 ]
                                }
                            },
                            {
                                "patchline": {
                                    "destination": [ "obj-81", 0 ],
                                    "source": [ "obj-85", 0 ]
                                }
                            }
                        ],
                        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "patching_rect": [ 748.666688978672, 132.00000393390656, 95.0, 22.0 ],
                    "saved_object_attributes": {
                        "fontsize": 10.0,
                        "locked_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
                    },
                    "text": "p EncoderCount"
                }
            },
            {
                "box": {
                    "id": "obj-215",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1151.3333676457405, 62.66666853427887, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 995.0, 289.0, 99.0, 34.0 ],
                    "text": "AUDIO ENGINE ON/OFF",
                    "textcolor": [ 0.0, 0.0, 0.0, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-212",
                    "local": 1,
                    "maxclass": "ezdac~",
                    "numinlets": 2,
                    "numoutlets": 0,
                    "patching_rect": [ 1106.6666996479034, 54.66666829586029, 44.0, 44.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 950.0, 281.0, 44.0, 44.0 ],
                    "prototypename": "helpfile"
                }
            },
            {
                "box": {
                    "id": "obj-163",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1130.6667003631592, 558.0000166296959, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 1158.0, 143.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 13\nC.mdlr2.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-167",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 948.6666949391365, 558.6666833162308, 105.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 976.0, 144.0, 105.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 12\ncasioVl1.beat.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-172",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 767.3333562016487, 560.6666833758354, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 795.0, 146.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 11\nG.mdlr2.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-176",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 574.6666837930679, 560.6666833758354, 121.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 602.0, 146.0, 121.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 10\nbass.ArpMagnet.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-180",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 403.33334535360336, 562.6666834354401, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 431.0, 148.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 9\nKickHat.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-135",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 1323.33337277174, 54.66666829586029, 125.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 963.0, 384.0, 125.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "MUSIC\nFADE IN / FADE OUT",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-47",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 948.6666949391365, 440.00001311302185, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 980.0, 37.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 6\nMallet.vfm.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-48",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 764.6666894555092, 440.00001311302185, 107.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 796.0, 37.0, 107.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 5 shakerswings.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-50",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 581.3333506584167, 440.00001311302185, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 613.0, 37.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 4\npercClacks1.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-53",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 383.3333447575569, 438.6666797399521, 142.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 415.0, 36.0, 142.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 3\nsteel.bowls.slow.ALT.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-54",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 212.66667300462723, 438.6666797399521, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 244.0, 36.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 2\n tone.31.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "id": "obj-123",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [ 34.66666769981384, 436.00001299381256, 99.0, 34.0 ],
                    "presentation": 1,
                    "presentation_linecount": 2,
                    "presentation_rect": [ 66.0, 33.0, 99.0, 34.0 ],
                    "saved_attribute_attributes": {
                        "textcolor": {
                            "expression": "themecolor.live_meter_bg"
                        }
                    },
                    "text": "Sample 1 tone.50.wav",
                    "textcolor": [ 0.079348079365577, 0.07934804057877, 0.079348050547289, 1.0 ],
                    "textjustification": 1
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-130",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 9.333333611488342, 466.6666805744171, 149.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 41.0, 64.0, 149.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-260",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 918.6666940450668, 470.6666806936264, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 950.0, 68.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-261",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 738.6666886806488, 470.6666806936264, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 770.0, 68.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-262",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 377.333344578743, 594.0000177025795, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 405.0, 179.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-263",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 555.3333498835564, 594.0000177025795, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 583.0, 179.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-264",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 741.3333554267883, 592.0000176429749, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 769.0, 177.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "attr": "buffername",
                    "id": "obj-265",
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 922.6666941642761, 592.0000176429749, 150.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 950.0, 177.0, 150.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-28",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 575.3333504796028, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 599.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-29",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 519.3333488106728, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 631.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-30",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 519.3333488106728, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-31",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 487.33334785699844, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 492.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-32",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 431.3333461880684, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 524.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-33",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 431.3333461880684, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-34",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 399.3333452343941, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 385.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-35",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 343.333343565464, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 417.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-36",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 343.333343565464, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-37",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 311.3333426117897, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 275.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-38",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 255.33334094285965, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 308.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-39",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 255.33334094285965, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-40",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 223.33333998918533, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 170.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-41",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 167.33333832025528, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 203.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-42",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 167.33333832025528, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-43",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 135.33333736658096, 342.00001019239426, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 57.0, 560.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-44",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 79.33333569765091, 342.66667687892914, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 92.0, 561.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-45",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 79.33333569765091, 302.00000900030136, 75.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-25",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 526.6666823625565, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 609.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-26",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 469.33334732055664, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 641.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-27",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 469.33334732055664, 172.66667181253433, 76.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-22",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 438.6666797399521, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 495.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-23",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 381.33334469795227, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 527.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-24",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 381.33334469795227, 172.66667181253433, 76.0, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-19",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 350.6666771173477, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 385.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-20",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 293.3333420753479, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 420.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-21",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 293.3333420753479, 172.66667181253433, 76.00000166893005, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-16",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 262.66667449474335, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 276.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-17",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 205.33333945274353, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 311.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-18",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 205.33333945274353, 172.66667181253433, 76.00000166893005, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-13",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 174.66667187213898, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 174.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-14",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 117.33333683013916, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 206.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-15",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 117.33333683013916, 172.66667181253433, 76.00000166893005, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-12",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 86.6666692495346, 210.66667294502258, 24.0, 24.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 60.0, 383.0, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-10",
                    "maxclass": "number",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "", "bang" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 29.33333420753479, 210.66667294502258, 50.0, 22.0 ],
                    "presentation": 1,
                    "presentation_rect": [ 91.0, 384.0, 50.0, 22.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-6",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "int", "int" ],
                    "patching_rect": [ 29.33333420753479, 172.66667181253433, 76.00000166893005, 22.0 ],
                    "text": "wakemove"
                }
            },
            {
                "box": {
                    "id": "obj-4",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "patching_rect": [ 34.66666769981384, 66.00000196695328, 56.0, 22.0 ],
                    "text": "metro 10"
                }
            },
            {
                "box": {
                    "id": "obj-3",
                    "maxclass": "toggle",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "parameter_enable": 0,
                    "patching_rect": [ 34.66666769981384, 24.66666740179062, 24.0, 24.0 ]
                }
            },
            {
                "box": {
                    "id": "obj-1",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 12,
                    "outlettype": [ "", "", "", "", "", "", "", "", "", "", "", "" ],
                    "patching_rect": [ 34.66666769981384, 100.66666966676712, 506.0, 22.0 ],
                    "text": "encoderin c d"
                }
            }
        ],
        "lines": [
            {
                "patchline": {
                    "destination": [ "obj-15", 0 ],
                    "midpoints": [ 88.43939497254112, 160.0000086426735, 126.83333683013916, 160.0000086426735 ],
                    "source": [ "obj-1", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-18", 0 ],
                    "midpoints": [ 132.7121222452684, 160.0000086426735, 214.83333945274353, 160.0000086426735 ],
                    "source": [ "obj-1", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-21", 0 ],
                    "midpoints": [ 176.98484951799566, 160.0000086426735, 302.8333420753479, 160.0000086426735 ],
                    "source": [ "obj-1", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-24", 0 ],
                    "midpoints": [ 221.25757679072294, 160.0000086426735, 390.83334469795227, 160.0000086426735 ],
                    "source": [ "obj-1", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-27", 0 ],
                    "midpoints": [ 265.5303040634502, 160.0000086426735, 478.83334732055664, 160.0000086426735 ],
                    "source": [ "obj-1", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-30", 0 ],
                    "midpoints": [ 531.1666676998138, 160.0000086426735, 560.3333485722542, 160.0000086426735, 560.3333485722542, 288.2617273926735, 528.8333488106728, 288.2617273926735 ],
                    "source": [ "obj-1", 11 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-33", 0 ],
                    "midpoints": [ 486.8939404270866, 160.0000086426735, 560.9544423222542, 160.0000086426735, 560.9544423222542, 288.6211023926735, 440.8333461880684, 288.6211023926735 ],
                    "source": [ "obj-1", 10 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-36", 0 ],
                    "midpoints": [ 442.6212131543593, 160.0000086426735, 559.9192860722542, 160.0000086426735, 559.9192860722542, 287.6523523926735, 352.833343565464, 287.6523523926735 ],
                    "source": [ "obj-1", 9 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-39", 0 ],
                    "midpoints": [ 398.34848588163203, 160.0000086426735, 560.7122548222542, 160.0000086426735, 560.7122548222542, 288.3164148926735, 264.83334094285965, 288.3164148926735 ],
                    "source": [ "obj-1", 8 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-42", 0 ],
                    "midpoints": [ 354.0757586089048, 160.0000086426735, 560.0833485722542, 160.0000086426735, 560.0833485722542, 288.3671961426735, 176.83333832025528, 288.3671961426735 ],
                    "source": [ "obj-1", 7 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-45", 0 ],
                    "midpoints": [ 309.80303133617747, 160.0000086426735, 560.5286610722542, 160.0000086426735, 560.5286610722542, 287.6757898926735, 88.83333569765091, 287.6757898926735 ],
                    "source": [ "obj-1", 6 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-6", 0 ],
                    "midpoints": [ 44.16666769981384, 169.0000086426735, 38.83333420753479, 169.0000086426735 ],
                    "source": [ "obj-1", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-106", 0 ],
                    "source": [ "obj-10", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-103", 0 ],
                    "source": [ "obj-101", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-100", 0 ],
                    "source": [ "obj-103", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-103", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-124", 0 ],
                    "source": [ "obj-105", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-71", 0 ],
                    "midpoints": [ 872.8333590626717, 309.00001138448715, 758.166688978672, 309.00001138448715 ],
                    "order": 1,
                    "source": [ "obj-107", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-98", 0 ],
                    "midpoints": [ 872.8333590626717, 152.97657388448715, 958.1666949391365, 152.97657388448715 ],
                    "order": 0,
                    "source": [ "obj-107", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-57", 1 ],
                    "source": [ "obj-11", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-57", 0 ],
                    "source": [ "obj-11", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-126", 0 ],
                    "source": [ "obj-118", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-107", 0 ],
                    "order": 0,
                    "source": [ "obj-121", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-279", 0 ],
                    "midpoints": [ 872.8333590626717, 105.00001138448715, 702.8333539962769, 105.00001138448715 ],
                    "order": 1,
                    "source": [ "obj-121", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-104", 0 ],
                    "source": [ "obj-124", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-124", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-98", 0 ],
                    "source": [ "obj-126", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-128", 0 ],
                    "source": [ "obj-130", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-108", 0 ],
                    "source": [ "obj-14", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-57", 1 ],
                    "source": [ "obj-142", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-57", 0 ],
                    "source": [ "obj-142", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-211", 0 ],
                    "midpoints": [ 1308.1667053699493, 101.60001138448717, 1386.1667076945305, 101.60001138448717 ],
                    "order": 0,
                    "source": [ "obj-143", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-213", 0 ],
                    "order": 1,
                    "source": [ "obj-143", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-13", 0 ],
                    "source": [ "obj-15", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-14", 0 ],
                    "source": [ "obj-15", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-136", 0 ],
                    "source": [ "obj-154", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-109", 0 ],
                    "source": [ "obj-17", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-16", 0 ],
                    "source": [ "obj-18", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-17", 0 ],
                    "source": [ "obj-18", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-58", 0 ],
                    "source": [ "obj-181", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-110", 0 ],
                    "source": [ "obj-20", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-194", 0 ],
                    "source": [ "obj-207", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-208", 0 ],
                    "source": [ "obj-209", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-19", 0 ],
                    "source": [ "obj-21", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-20", 0 ],
                    "source": [ "obj-21", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-112", 0 ],
                    "source": [ "obj-211", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-115", 0 ],
                    "source": [ "obj-213", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-222", 0 ],
                    "source": [ "obj-223", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-224", 0 ],
                    "source": [ "obj-225", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-111", 0 ],
                    "source": [ "obj-23", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-22", 0 ],
                    "source": [ "obj-24", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-23", 0 ],
                    "source": [ "obj-24", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-113", 0 ],
                    "source": [ "obj-26", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-226", 0 ],
                    "source": [ "obj-260", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-220", 0 ],
                    "source": [ "obj-261", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-236", 0 ],
                    "source": [ "obj-262", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-234", 0 ],
                    "source": [ "obj-263", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-232", 0 ],
                    "source": [ "obj-264", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-230", 0 ],
                    "source": [ "obj-265", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-25", 0 ],
                    "source": [ "obj-27", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-26", 0 ],
                    "source": [ "obj-27", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-58", 0 ],
                    "midpoints": [ 702.8333539962769, 213.00001138448715, 758.166688978672, 213.00001138448715 ],
                    "source": [ "obj-279", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-114", 0 ],
                    "source": [ "obj-29", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-4", 0 ],
                    "source": [ "obj-3", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-28", 0 ],
                    "source": [ "obj-30", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-29", 0 ],
                    "source": [ "obj-30", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-71", 0 ],
                    "source": [ "obj-307", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-71", 0 ],
                    "midpoints": [ 664.8333528637886, 309.00001138448715, 758.166688978672, 309.00001138448715 ],
                    "source": [ "obj-308", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-116", 0 ],
                    "source": [ "obj-32", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-31", 0 ],
                    "source": [ "obj-33", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-32", 0 ],
                    "source": [ "obj-33", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-117", 0 ],
                    "source": [ "obj-35", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-34", 0 ],
                    "source": [ "obj-36", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-35", 0 ],
                    "source": [ "obj-36", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-119", 0 ],
                    "source": [ "obj-38", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-37", 0 ],
                    "source": [ "obj-39", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-38", 0 ],
                    "source": [ "obj-39", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-401", 0 ],
                    "source": [ "obj-399", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-1", 0 ],
                    "source": [ "obj-4", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-8", 0 ],
                    "source": [ "obj-401", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-120", 0 ],
                    "source": [ "obj-41", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-40", 0 ],
                    "source": [ "obj-42", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-41", 0 ],
                    "source": [ "obj-42", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-122", 0 ],
                    "source": [ "obj-44", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-43", 0 ],
                    "source": [ "obj-45", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-44", 0 ],
                    "source": [ "obj-45", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-51", 0 ],
                    "source": [ "obj-49", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-2", 0 ],
                    "source": [ "obj-5", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-51", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-46", 0 ],
                    "source": [ "obj-51", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-169", 1 ],
                    "source": [ "obj-57", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-169", 0 ],
                    "midpoints": [ 533.5, 1237.4999995827675, 533.5, 1237.4999995827675 ],
                    "source": [ "obj-57", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-307", 0 ],
                    "source": [ "obj-58", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-589", 0 ],
                    "source": [ "obj-597", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-10", 0 ],
                    "source": [ "obj-6", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-12", 0 ],
                    "source": [ "obj-6", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-103", 1 ],
                    "source": [ "obj-68", 7 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-124", 1 ],
                    "source": [ "obj-68", 6 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-142", 1 ],
                    "source": [ "obj-68", 13 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-142", 0 ],
                    "source": [ "obj-68", 12 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-51", 1 ],
                    "source": [ "obj-68", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-72", 1 ],
                    "source": [ "obj-68", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-75", 1 ],
                    "source": [ "obj-68", 2 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-78", 1 ],
                    "source": [ "obj-68", 3 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-81", 1 ],
                    "source": [ "obj-68", 4 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-84", 1 ],
                    "source": [ "obj-68", 5 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-87", 1 ],
                    "source": [ "obj-68", 11 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-91", 1 ],
                    "source": [ "obj-68", 10 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-94", 1 ],
                    "source": [ "obj-68", 9 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-97", 1 ],
                    "source": [ "obj-68", 8 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-72", 0 ],
                    "source": [ "obj-70", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-492", 0 ],
                    "source": [ "obj-71", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-72", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-69", 0 ],
                    "source": [ "obj-72", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-75", 0 ],
                    "source": [ "obj-74", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-75", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-73", 0 ],
                    "source": [ "obj-75", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-78", 0 ],
                    "source": [ "obj-77", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-78", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-76", 0 ],
                    "source": [ "obj-78", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-81", 0 ],
                    "source": [ "obj-80", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-81", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-79", 0 ],
                    "source": [ "obj-81", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-84", 0 ],
                    "source": [ "obj-83", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-84", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-82", 0 ],
                    "source": [ "obj-84", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-87", 0 ],
                    "source": [ "obj-86", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-87", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-85", 0 ],
                    "source": [ "obj-87", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-181", 0 ],
                    "source": [ "obj-88", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-91", 0 ],
                    "source": [ "obj-90", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-91", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-89", 0 ],
                    "source": [ "obj-91", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-94", 0 ],
                    "source": [ "obj-93", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 1 ],
                    "source": [ "obj-94", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-92", 0 ],
                    "source": [ "obj-94", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-97", 0 ],
                    "source": [ "obj-96", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-11", 0 ],
                    "source": [ "obj-97", 0 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-95", 0 ],
                    "source": [ "obj-97", 1 ]
                }
            },
            {
                "patchline": {
                    "destination": [ "obj-399", 0 ],
                    "source": [ "obj-98", 0 ]
                }
            }
        ],
        "parameters": {
            "obj-103::obj-33::obj-31": [ "number[31]", "number[4]", 0 ],
            "obj-103::obj-33::obj-75": [ "number[29]", "number[1]", 0 ],
            "obj-103::obj-33::obj-9": [ "mc.live.gain~[9]", "grains", 0 ],
            "obj-103::obj-33::obj-94": [ "number[30]", "number[1]", 0 ],
            "obj-11": [ "live.gain~", "live.gain~", 0 ],
            "obj-124::obj-33::obj-31": [ "number[28]", "number[4]", 0 ],
            "obj-124::obj-33::obj-75": [ "number[27]", "number[1]", 0 ],
            "obj-124::obj-33::obj-9": [ "mc.live.gain~[8]", "grains", 0 ],
            "obj-124::obj-33::obj-94": [ "number[26]", "number[1]", 0 ],
            "obj-142": [ "live.gain~[24]", "live.gain~[24]", 0 ],
            "obj-51::obj-33::obj-31": [ "number[4]", "number[4]", 0 ],
            "obj-51::obj-33::obj-75": [ "number[1]", "number[1]", 0 ],
            "obj-51::obj-33::obj-9": [ "mc.live.gain~", "grains", 0 ],
            "obj-51::obj-33::obj-94": [ "number[6]", "number[1]", 0 ],
            "obj-68::obj-23": [ "live.gain~[1]", "g", 0 ],
            "obj-68::obj-24": [ "live.gain~[2]", "g", 0 ],
            "obj-68::obj-25": [ "live.gain~[3]", "g", 0 ],
            "obj-68::obj-26": [ "live.gain~[4]", "g", 0 ],
            "obj-68::obj-27": [ "live.gain~[5]", "g", 0 ],
            "obj-68::obj-28": [ "live.gain~[6]", "g", 0 ],
            "obj-68::obj-29": [ "live.gain~[7]", "g", 0 ],
            "obj-68::obj-30": [ "live.gain~[8]", "g", 0 ],
            "obj-68::obj-31": [ "live.gain~[9]", "g", 0 ],
            "obj-68::obj-32": [ "live.gain~[10]", "g", 0 ],
            "obj-68::obj-33": [ "live.gain~[11]", "g", 0 ],
            "obj-68::obj-34": [ "live.gain~[12]", "g", 0 ],
            "obj-68::obj-35": [ "live.gain~[13]", "g", 0 ],
            "obj-68::obj-36": [ "live.gain~[14]", "g", 0 ],
            "obj-68::obj-37": [ "live.gain~[15]", "g", 0 ],
            "obj-68::obj-38": [ "live.gain~[16]", "g", 0 ],
            "obj-68::obj-39": [ "live.gain~[17]", "g", 0 ],
            "obj-68::obj-40": [ "live.gain~[18]", "g", 0 ],
            "obj-68::obj-41": [ "live.gain~[19]", "g", 0 ],
            "obj-68::obj-42": [ "live.gain~[20]", "g", 0 ],
            "obj-68::obj-43": [ "live.gain~[21]", "g", 0 ],
            "obj-68::obj-44": [ "live.gain~[22]", "g", 0 ],
            "obj-68::obj-45": [ "live.gain~[23]", "live.gain~[23]", 0 ],
            "obj-72::obj-33::obj-31": [ "number[14]", "number[4]", 0 ],
            "obj-72::obj-33::obj-75": [ "number[13]", "number[1]", 0 ],
            "obj-72::obj-33::obj-9": [ "mc.live.gain~[3]", "grains", 0 ],
            "obj-72::obj-33::obj-94": [ "number[11]", "number[1]", 0 ],
            "obj-75::obj-33::obj-31": [ "number[16]", "number[4]", 0 ],
            "obj-75::obj-33::obj-75": [ "number[15]", "number[1]", 0 ],
            "obj-75::obj-33::obj-9": [ "mc.live.gain~[4]", "grains", 0 ],
            "obj-75::obj-33::obj-94": [ "number[12]", "number[1]", 0 ],
            "obj-78::obj-33::obj-31": [ "number[19]", "number[4]", 0 ],
            "obj-78::obj-33::obj-75": [ "number[17]", "number[1]", 0 ],
            "obj-78::obj-33::obj-9": [ "mc.live.gain~[5]", "grains", 0 ],
            "obj-78::obj-33::obj-94": [ "number[18]", "number[1]", 0 ],
            "obj-81::obj-33::obj-31": [ "number[22]", "number[4]", 0 ],
            "obj-81::obj-33::obj-75": [ "number[21]", "number[1]", 0 ],
            "obj-81::obj-33::obj-9": [ "mc.live.gain~[6]", "grains", 0 ],
            "obj-81::obj-33::obj-94": [ "number[20]", "number[1]", 0 ],
            "obj-84::obj-33::obj-31": [ "number[23]", "number[4]", 0 ],
            "obj-84::obj-33::obj-75": [ "number[25]", "number[1]", 0 ],
            "obj-84::obj-33::obj-9": [ "mc.live.gain~[7]", "grains", 0 ],
            "obj-84::obj-33::obj-94": [ "number[24]", "number[1]", 0 ],
            "obj-87::obj-33::obj-31": [ "number[43]", "number[4]", 0 ],
            "obj-87::obj-33::obj-75": [ "number[42]", "number[1]", 0 ],
            "obj-87::obj-33::obj-9": [ "mc.live.gain~[13]", "grains", 0 ],
            "obj-87::obj-33::obj-94": [ "number[41]", "number[1]", 0 ],
            "obj-91::obj-33::obj-31": [ "number[40]", "number[4]", 0 ],
            "obj-91::obj-33::obj-75": [ "number[38]", "number[1]", 0 ],
            "obj-91::obj-33::obj-9": [ "mc.live.gain~[12]", "grains", 0 ],
            "obj-91::obj-33::obj-94": [ "number[39]", "number[1]", 0 ],
            "obj-94::obj-33::obj-31": [ "number[36]", "number[4]", 0 ],
            "obj-94::obj-33::obj-75": [ "number[37]", "number[1]", 0 ],
            "obj-94::obj-33::obj-9": [ "mc.live.gain~[11]", "grains", 0 ],
            "obj-94::obj-33::obj-94": [ "number[35]", "number[1]", 0 ],
            "obj-97::obj-33::obj-31": [ "number[33]", "number[4]", 0 ],
            "obj-97::obj-33::obj-75": [ "number[34]", "number[1]", 0 ],
            "obj-97::obj-33::obj-9": [ "mc.live.gain~[10]", "grains", 0 ],
            "obj-97::obj-33::obj-94": [ "number[32]", "number[1]", 0 ],
            "parameterbanks": {
                "0": {
                    "index": 0,
                    "name": "",
                    "parameters": [ "-", "-", "-", "-", "-", "-", "-", "-" ],
                    "buttons": [ "-", "-", "-", "-", "-", "-", "-", "-" ]
                }
            },
            "parameter_overrides": {
                "obj-103::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[9]"
                },
                "obj-124::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[8]"
                },
                "obj-72::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[3]"
                },
                "obj-75::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[4]"
                },
                "obj-78::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[5]"
                },
                "obj-81::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[6]"
                },
                "obj-84::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[7]"
                },
                "obj-87::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[13]"
                },
                "obj-91::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[12]"
                },
                "obj-94::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[11]"
                },
                "obj-97::obj-33::obj-9": {
                    "parameter_longname": "mc.live.gain~[10]"
                }
            },
            "inherited_shortname": 1
        },
        "autosave": 0,
        "bgcolor": [ 1.0, 1.0, 1.0, 1.0 ],
        "stripecolor": [ 0.23529411764705882, 0.23529411764705882, 0.23529411764705882, 1.0 ],
        "editing_bgcolor": [ 1.0, 1.0, 1.0, 1.0 ]
    }
}