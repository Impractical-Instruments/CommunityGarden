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
		"rect" : [ 100, 100, 500, 560 ],
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
		"description" : "Stub synthesizer voice — sine oscillator with ADSR envelope. Inlet 0: MIDI pitch (0-127). Inlet 1: velocity (0-127). Inlet 2: gate (1=attack, 0=release). Outlets: L/R audio signal.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.synth — Stub Synthesizer Voice",
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
					"text" : "Sine oscillator + ADSR envelope. Swap cycle~ for a richer source when ready.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 40.0, 460.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 90.0, 30.0, 30.0 ],
					"comment" : "MIDI pitch (0-127)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 180.0, 90.0, 30.0, 30.0 ],
					"comment" : "velocity (0-127)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 330.0, 90.0, 30.0, 30.0 ],
					"comment" : "gate (1=attack, 0=release)"
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "MIDI pitch",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 96.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "velocity",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 96.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "comment",
					"text" : "gate",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 365.0, 96.0, 60.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "newobj",
					"text" : "mtof",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 30.0, 145.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"text" : "/ 127.",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 180.0, 145.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "newobj",
					"text" : "adsr~ 10 100 0.7 200",
					"numinlets" : 5,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 255.0, 145.0, 185.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "comment",
					"text" : "attack=10ms  decay=100ms  sustain=0.7  release=200ms",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 255.0, 170.0, 320.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "cycle~ 440",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 200.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "sig~",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 180.0, 200.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "freq via right inlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 125.0, 200.0, 130.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "newobj",
					"text" : "*~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 255.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "comment",
					"text" : "osc * envelope",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 85.0, 255.0, 110.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "newobj",
					"text" : "*~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 310.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "comment",
					"text" : "* velocity amplitude",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 85.0, 310.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "newobj",
					"text" : "*~ 0.5",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 365.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "comment",
					"text" : "safety headroom (-6 dB)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 100.0, 365.0, 180.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 425.0, 30.0, 30.0 ],
					"comment" : "audio L"
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 180.0, 425.0, 30.0, 30.0 ],
					"comment" : "audio R"
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "comment",
					"text" : "audio L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 431.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "comment",
					"text" : "audio R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 431.0, 80.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-3", 0 ],
					"destination" : [ "obj-9", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-4", 0 ],
					"destination" : [ "obj-10", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-11", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-9", 0 ],
					"destination" : [ "obj-13", 1 ],
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
					"source" : [ "obj-13", 0 ],
					"destination" : [ "obj-16", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-11", 0 ],
					"destination" : [ "obj-16", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-16", 0 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-18", 1 ],
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
					"source" : [ "obj-20", 0 ],
					"destination" : [ "obj-22", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-20", 0 ],
					"destination" : [ "obj-23", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
