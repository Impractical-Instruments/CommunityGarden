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
		"rect" : [ 100, 100, 720, 620 ],
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
		"description" : "4-channel spatial output stub. Inlets: L bus, R bus (stereo mix). Outlets: Ch1 front-L, Ch2 front-R, Ch3 rear-L, Ch4 rear-R. Stub distributes L->Ch1+Ch3, R->Ch2+Ch4 with rear attenuation. Replace *~ scalars with a proper panning matrix or spatialization library.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.spatial-out — 4-Channel Spatial Output (Stub)",
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
					"text" : "STUB: L→Ch1(front-L)+Ch3(rear-L), R→Ch2(front-R)+Ch4(rear-R). Rear channels attenuated by 0.5.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 40.0, 680.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "comment",
					"text" : "Replace scalar *~ with a proper pan matrix or IRCAM Spat / ICST Ambisonics for real spatialization.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 60.0, 680.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 100.0, 30.0, 30.0 ],
					"comment" : "L mix bus"
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 300.0, 100.0, 30.0, 30.0 ],
					"comment" : "R mix bus"
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "L mix bus",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 107.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "R mix bus",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 335.0, 107.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "comment",
					"text" : "── Front Channels ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 155.0, 180.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "newobj",
					"text" : "*~ 0.7",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 178.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"text" : "*~ 0.7",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 300.0, 178.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "comment",
					"text" : "Ch1: front-L (-3 dB)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 100.0, 182.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "comment",
					"text" : "Ch2: front-R (-3 dB)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 370.0, 182.0, 150.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "comment",
					"text" : "── Rear Channels ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 225.0, 180.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "*~ 0.5",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 248.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "newobj",
					"text" : "*~ 0.5",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 300.0, 248.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "comment",
					"text" : "Ch3: rear-L (-6 dB, attenuated stub)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 100.0, 252.0, 260.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "comment",
					"text" : "Ch4: rear-R (-6 dB, attenuated stub)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 370.0, 252.0, 260.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "comment",
					"text" : "── Master Limiter ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 298.0, 180.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "newobj",
					"text" : "clip~ -1. 1.",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 320.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "newobj",
					"text" : "clip~ -1. 1.",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 160.0, 320.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "newobj",
					"text" : "clip~ -1. 1.",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 290.0, 320.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "newobj",
					"text" : "clip~ -1. 1.",
					"numinlets" : 3,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 420.0, 320.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "comment",
					"text" : "hard clip at ±1.0 — replace with a proper brickwall limiter",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 348.0, 400.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 430.0, 30.0, 30.0 ],
					"comment" : "Ch1: front-L"
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 160.0, 430.0, 30.0, 30.0 ],
					"comment" : "Ch2: front-R"
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 290.0, 430.0, 30.0, 30.0 ],
					"comment" : "Ch3: rear-L"
				}
			},
			{
				"box" : 				{
					"id" : "obj-27",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 420.0, 430.0, 30.0, 30.0 ],
					"comment" : "Ch4: rear-R"
				}
			},
			{
				"box" : 				{
					"id" : "obj-28",
					"maxclass" : "comment",
					"text" : "Ch1 front-L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 437.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-29",
					"maxclass" : "comment",
					"text" : "Ch2 front-R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 195.0, 437.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-30",
					"maxclass" : "comment",
					"text" : "Ch3 rear-L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 325.0, 437.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-31",
					"maxclass" : "comment",
					"text" : "Ch4 rear-R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 455.0, 437.0, 90.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-4", 0 ],
					"destination" : [ "obj-9", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-10", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-4", 0 ],
					"destination" : [ "obj-14", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-15", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-9", 0 ],
					"destination" : [ "obj-19", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-10", 0 ],
					"destination" : [ "obj-20", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-21", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-15", 0 ],
					"destination" : [ "obj-22", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-19", 0 ],
					"destination" : [ "obj-24", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-20", 0 ],
					"destination" : [ "obj-25", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-21", 0 ],
					"destination" : [ "obj-26", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-22", 0 ],
					"destination" : [ "obj-27", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
