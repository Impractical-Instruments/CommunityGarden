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
		"rect" : [ 100, 100, 780, 620 ],
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
		"description" : "4-slot audio clip launcher. Inlet 0: slot trigger (int 1-4 to play, 0 to stop all). Outlets: L/R stereo audio mix. Slots use sfplay~ — load audio files by double-clicking each sfplay~ and choosing 'Set...'.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.audio-clip-launcher — 4-Slot Audio Clip Launcher",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 15.0, 480.0, 22.0 ],
					"fontsize" : 14.0,
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "comment",
					"text" : "Send int 1-4 to trigger a slot; 0 stops all. Load audio via each sfplay~ object's 'Set...' menu.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 40.0, 680.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 85.0, 30.0, 30.0 ],
					"comment" : "slot trigger: int 1-4 play, 0 stop all"
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "comment",
					"text" : "slot (1-4 play, 0 stop all)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 91.0, 200.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "newobj",
					"text" : "select 0 1 2 3 4",
					"numinlets" : 1,
					"numoutlets" : 6,
					"outlettype" : [ "bang", "bang", "bang", "bang", "bang", "" ],
					"patching_rect" : [ 30.0, 135.0, 150.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "outlet 0=stop-all  outlets 1-4=play slots  outlet 5=unmatched",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 195.0, 139.0, 450.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "── Slot 1 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 176.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "comment",
					"text" : "── Slot 2 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 176.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "comment",
					"text" : "── Slot 3 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 390.0, 176.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "comment",
					"text" : "── Slot 4 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 570.0, 176.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "newobj",
					"text" : "sfplay~ 2",
					"numinlets" : 3,
					"numoutlets" : 3,
					"outlettype" : [ "signal", "signal", "bang" ],
					"patching_rect" : [ 30.0, 200.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "newobj",
					"text" : "sfplay~ 2",
					"numinlets" : 3,
					"numoutlets" : 3,
					"outlettype" : [ "signal", "signal", "bang" ],
					"patching_rect" : [ 210.0, 200.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "sfplay~ 2",
					"numinlets" : 3,
					"numoutlets" : 3,
					"outlettype" : [ "signal", "signal", "bang" ],
					"patching_rect" : [ 390.0, 200.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "sfplay~ 2",
					"numinlets" : 3,
					"numoutlets" : 3,
					"outlettype" : [ "signal", "signal", "bang" ],
					"patching_rect" : [ 570.0, 200.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "sfplay~ 2 = stereo playback\nDouble-click → Set... to load audio file",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 228.0, 240.0, 36.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "newobj",
					"text" : "message stop",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 295.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "comment",
					"text" : "stop-all message",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 299.0, 130.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "comment",
					"text" : "── Mix ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 365.0, 80.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 390.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 90.0, 390.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 150.0, 390.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 435.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 90.0, 435.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 150.0, 435.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "comment",
					"text" : "L channels summed",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 439.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "comment",
					"text" : "R channels summed",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 394.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-27",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 505.0, 30.0, 30.0 ],
					"comment" : "audio L mix"
				}
			},
			{
				"box" : 				{
					"id" : "obj-28",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 180.0, 505.0, 30.0, 30.0 ],
					"comment" : "audio R mix"
				}
			},
			{
				"box" : 				{
					"id" : "obj-29",
					"maxclass" : "comment",
					"text" : "audio L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 511.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-30",
					"maxclass" : "comment",
					"text" : "audio R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 511.0, 80.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-3", 0 ],
					"destination" : [ "obj-5", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-16", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 1 ],
					"destination" : [ "obj-11", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 2 ],
					"destination" : [ "obj-12", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 3 ],
					"destination" : [ "obj-13", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 4 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-11", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-12", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-13", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-11", 0 ],
					"destination" : [ "obj-19", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-12", 0 ],
					"destination" : [ "obj-19", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-19", 0 ],
					"destination" : [ "obj-21", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 0 ],
					"destination" : [ "obj-20", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-20", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-20", 0 ],
					"destination" : [ "obj-21", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-11", 1 ],
					"destination" : [ "obj-22", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-12", 1 ],
					"destination" : [ "obj-22", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-22", 0 ],
					"destination" : [ "obj-24", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 1 ],
					"destination" : [ "obj-23", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 1 ],
					"destination" : [ "obj-23", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-23", 0 ],
					"destination" : [ "obj-24", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-21", 0 ],
					"destination" : [ "obj-27", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-24", 0 ],
					"destination" : [ "obj-28", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
