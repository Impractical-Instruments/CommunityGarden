{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 8,
			"minor" : 6,
			"revision" : 2,
			"architecture" : "x64",
			"modernui" : 1
		},
		"classnamespace" : "dsp.toplevel",
		"rect" : [ 100, 100, 640, 500 ],
		"bglocked" : 0,
		"openinpresentation" : 0,
		"default_fontsize" : 12.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaptoobjects" : 0,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"description" : "OSC input handler. Listens on UDP port 9001. Routes /pp/encoder and /pp/switch messages. Outlet 0: encoder data [num val]. Outlet 1: switch data [num val].",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.osc-in — OSC Input Handler",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 15.0, 400.0, 22.0 ],
					"fontsize" : 14.0,
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "comment",
					"text" : "Receives OSC over UDP on port 9001. No inlets — self-contained receiver.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 40.0, 560.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "comment",
					"text" : "Expected OSC address format:",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 63.0, 220.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "comment",
					"text" : "  /pp/encoder [1-8] [0.0-1.0]    — continuous rotary encoder (water valve)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 81.0, 500.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "comment",
					"text" : "  /pp/switch  [1-8] [0 or 1]     — momentary electrical switch",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 99.0, 500.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "newobj",
					"text" : "udpreceive 9001",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 135.0, 135.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "listen on UDP port 9001",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 175.0, 139.0, 200.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "newobj",
					"text" : "oscparse",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 180.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "comment",
					"text" : "parse OSC bundle → address + args list",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 115.0, 184.0, 280.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"text" : "route /pp/encoder /pp/switch",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "", "", "" ],
					"patching_rect" : [ 30.0, 225.0, 240.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "comment",
					"text" : "outlet 2 = unmatched (ignore or log)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 280.0, 229.0, 280.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "comment",
					"text" : "── Encoders ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 268.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "comment",
					"text" : "── Switches ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 340.0, 268.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "unpack i f",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "float" ],
					"patching_rect" : [ 30.0, 290.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "encoder num (1-8), value (0.0-1.0)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 294.0, 260.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "newobj",
					"text" : "unpack i i",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 340.0, 290.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "comment",
					"text" : "switch num (1-8), state (0 or 1)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 440.0, 294.0, 260.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "newobj",
					"text" : "pack i f",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 340.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "newobj",
					"text" : "pack i i",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 340.0, 340.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 400.0, 30.0, 30.0 ],
					"comment" : "encoder data: list [num val]"
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 340.0, 400.0, 30.0, 30.0 ],
					"comment" : "switch data: list [num state]"
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "comment",
					"text" : "encoder [num val]",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 407.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "comment",
					"text" : "switch [num state]",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 375.0, 407.0, 150.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-6", 0 ],
					"destination" : [ "obj-8", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-8", 0 ],
					"destination" : [ "obj-10", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-10", 0 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-10", 1 ],
					"destination" : [ "obj-16", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 1 ],
					"destination" : [ "obj-18", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-19", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 1 ],
					"destination" : [ "obj-19", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-20", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-19", 0 ],
					"destination" : [ "obj-21", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
