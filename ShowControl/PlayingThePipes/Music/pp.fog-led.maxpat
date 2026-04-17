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
		"rect" : [ 100, 100, 700, 580 ],
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
		"description" : "Fog machine and LED control stubs. Inlet 0: fog trigger (bang or 1/0). Inlet 1: LED intensity (0.0-1.0 from encoder). Fog sends OSC via UDP; LED sends MIDI CC. Update IPs and channels to match hardware.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.fog-led — Fog Machine & LED Control (Stub)",
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
					"text" : "Fog: OSC /pp/fog/on|off → UDP target. LED: MIDI CC 1 ch.1 → MIDI out. Update addresses to match hardware.",
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
					"comment" : "fog trigger (bang, or 1=on / 0=off)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 400.0, 85.0, 30.0, 30.0 ],
					"comment" : "LED intensity (0.0-1.0)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "comment",
					"text" : "fog trigger",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 91.0, 100.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "LED intensity (0.0-1.0)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 435.0, 91.0, 180.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "── Fog Machine ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 135.0, 160.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "newobj",
					"text" : "select 0 1",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "bang", "bang", "" ],
					"patching_rect" : [ 30.0, 157.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "comment",
					"text" : "or send a bang → outlet 1 (treated as on)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 161.0, 300.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"text" : "message /pp/fog/off",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "newobj",
					"text" : "message /pp/fog/on",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 210.0, 200.0, 165.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "newobj",
					"text" : "oscformat",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 245.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "oscformat",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 210.0, 245.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "udpsend 192.168.1.100 9002",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 290.0, 210.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "update IP + port to match fog controller",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 250.0, 294.0, 300.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "comment",
					"text" : "── LEDs ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 400.0, 135.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "newobj",
					"text" : "* 127.",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 400.0, 157.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "newobj",
					"text" : "int",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 400.0, 200.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "comment",
					"text" : "scale 0.0-1.0 → 0-127 for MIDI CC",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 460.0, 161.0, 250.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "newobj",
					"text" : "ctlout 1 1",
					"numinlets" : 3,
					"numoutlets" : 0,
					"patching_rect" : [ 400.0, 245.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "comment",
					"text" : "MIDI CC#1 on channel 1 → LED driver",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 500.0, 249.0, 280.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "comment",
					"text" : "ctlout ccnum channel — update to match LED hardware",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 400.0, 270.0, 340.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "comment",
					"text" : "── Timing Safety ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 340.0, 160.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "newobj",
					"text" : "timer",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 30.0, 362.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "newobj",
					"text" : "> 500",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 100.0, 362.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "comment",
					"text" : "Prevents re-triggering fog faster than 500ms. Connect fog on/off to timer inlets if needed.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 170.0, 366.0, 480.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-3", 0 ],
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
					"source" : [ "obj-8", 1 ],
					"destination" : [ "obj-11", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-10", 0 ],
					"destination" : [ "obj-12", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-11", 0 ],
					"destination" : [ "obj-13", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-12", 0 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 0 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-4", 0 ],
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-17", 0 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-20", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
