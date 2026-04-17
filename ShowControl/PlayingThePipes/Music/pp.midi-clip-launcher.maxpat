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
		"rect" : [ 100, 100, 720, 600 ],
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
		"description" : "4-slot MIDI clip launcher. Inlet 0: slot trigger (int 1-4 play, 0 stop all). Outlet 0: MIDI pitch, Outlet 1: velocity (0=note-off), Outlet 2: gate (1=on, 0=off). Stub slots use makenote — replace with seq or mtr for real sequences.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.midi-clip-launcher — 4-Slot MIDI Clip Launcher",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 15.0, 500.0, 22.0 ],
					"fontsize" : 14.0,
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "comment",
					"text" : "STUB: each slot fires a single makenote. Replace with seq or mtr objects for real MIDI sequences.",
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
					"text" : "outlet 0=stop  1-4=play slots",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 195.0, 139.0, 250.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "── Slot 1: C4 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 176.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "comment",
					"text" : "── Slot 2: E4 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 176.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "comment",
					"text" : "── Slot 3: G4 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 390.0, 176.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "comment",
					"text" : "── Slot 4: C5 ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 570.0, 176.0, 130.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "newobj",
					"text" : "makenote 60 100 1000",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 30.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "newobj",
					"text" : "makenote 64 90 800",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 210.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "makenote 67 80 600",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 390.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "makenote 72 100 400",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 570.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "makenote pitch vel dur(ms)\nReplace with seq for real clip playback",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 230.0, 240.0, 36.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "comment",
					"text" : "── Merge pitch + velocity ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 298.0, 220.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "newobj",
					"text" : "funnel 4",
					"numinlets" : 4,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 320.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "newobj",
					"text" : "funnel 4",
					"numinlets" : 4,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 180.0, 320.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "comment",
					"text" : "pitch from all 4 slots",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 115.0, 324.0, 160.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "comment",
					"text" : "velocity from all 4 slots (0 = note-off)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 265.0, 324.0, 280.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "comment",
					"text" : "── Derive gate from velocity ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 370.0, 240.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "newobj",
					"text" : "> 0",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 180.0, 392.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "comment",
					"text" : "1 when note-on, 0 when note-off",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 235.0, 396.0, 250.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 460.0, 30.0, 30.0 ],
					"comment" : "MIDI pitch"
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 180.0, 460.0, 30.0, 30.0 ],
					"comment" : "velocity (0=note-off)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 330.0, 460.0, 30.0, 30.0 ],
					"comment" : "gate (1=on, 0=off)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-27",
					"maxclass" : "comment",
					"text" : "pitch",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 466.0, 60.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-28",
					"maxclass" : "comment",
					"text" : "velocity",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 466.0, 60.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-29",
					"maxclass" : "comment",
					"text" : "gate",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 365.0, 466.0, 60.0, 18.0 ]
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
					"source" : [ "obj-11", 0 ],
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-12", 0 ],
					"destination" : [ "obj-17", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 0 ],
					"destination" : [ "obj-17", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-17", 3 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-11", 1 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-12", 1 ],
					"destination" : [ "obj-18", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 1 ],
					"destination" : [ "obj-18", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 1 ],
					"destination" : [ "obj-18", 3 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-22", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-17", 0 ],
					"destination" : [ "obj-24", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-25", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-22", 0 ],
					"destination" : [ "obj-26", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
