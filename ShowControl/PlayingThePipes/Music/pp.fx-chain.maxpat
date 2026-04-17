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
		"rect" : [ 100, 100, 680, 680 ],
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
		"description" : "Stereo audio effects chain stub: gain -> high-pass filter -> reverb (freeverb~) -> delay (tapin~/tapout~). Inlets: L/R audio. Outlets: L/R audio.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "pp.fx-chain — Track Effects Chain (Stub)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 15.0, 420.0, 22.0 ],
					"fontsize" : 14.0,
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "comment",
					"text" : "Signal path: gain~ → hip~ (HPF) → freeverb~ (reverb) → tapin~/tapout~ (delay).",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 40.0, 630.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "comment",
					"text" : "Replace hip~ with biquad~ or cascade~ for a full parametric EQ.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 15.0, 60.0, 580.0, 18.0 ]
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
					"comment" : "audio in L"
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "inlet",
					"numinlets" : 0,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 180.0, 100.0, 30.0, 30.0 ],
					"comment" : "audio in R"
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "audio in L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 107.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "comment",
					"text" : "audio in R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 107.0, 80.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "comment",
					"text" : "── Gain ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 152.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "newobj",
					"text" : "gain~ 2",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 175.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "newobj",
					"text" : "gain~ 2",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 180.0, 175.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "comment",
					"text" : "gain~ 2 = 2-inlet variant (audio + gain factor)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 255.0, 179.0, 340.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "comment",
					"text" : "── High-Pass Filter (DC block / rumble cut) ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 215.0, 360.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "hip~ 40",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 238.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "newobj",
					"text" : "hip~ 40",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 180.0, 238.0, 75.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "comment",
					"text" : "40 Hz HPF — swap for biquad~ for full EQ",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 270.0, 242.0, 320.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "comment",
					"text" : "── Reverb ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 278.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "newobj",
					"text" : "freeverb~",
					"numinlets" : 4,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "signal" ],
					"patching_rect" : [ 30.0, 300.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "comment",
					"text" : "freeverb~ inlets: L, R, room-size(0-1), damping(0-1)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 304.0, 430.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "newobj",
					"text" : "flonum",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 30.0, 330.0, 60.0, 22.0 ],
					"parameter_enable" : 1,
					"saved_attribute_attributes" : 				{
						"valueof" : 					{
							"parameter_initial" : [ 0.5 ],
							"parameter_initial_enable" : 1,
							"parameter_longname" : "room_size",
							"parameter_shortname" : "room",
							"parameter_type" : 0
						}
					}
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "newobj",
					"text" : "flonum",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "float" ],
					"patching_rect" : [ 100.0, 330.0, 60.0, 22.0 ],
					"parameter_enable" : 1,
					"saved_attribute_attributes" : 				{
						"valueof" : 					{
							"parameter_initial" : [ 0.5 ],
							"parameter_initial_enable" : 1,
							"parameter_longname" : "damping",
							"parameter_shortname" : "damp",
							"parameter_type" : 0
						}
					}
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "comment",
					"text" : "room size",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 355.0, 75.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "comment",
					"text" : "damping",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 100.0, 355.0, 75.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "comment",
					"text" : "── Delay ──",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 385.0, 100.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "newobj",
					"text" : "tapin~ 1000",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "tapconnect" ],
					"patching_rect" : [ 30.0, 407.0, 105.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "newobj",
					"text" : "tapin~ 1000",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "tapconnect" ],
					"patching_rect" : [ 180.0, 407.0, 105.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "newobj",
					"text" : "tapout~ 250.",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 452.0, 100.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-27",
					"maxclass" : "newobj",
					"text" : "tapout~ 250.",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 180.0, 452.0, 100.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-28",
					"maxclass" : "comment",
					"text" : "1000ms buffer, 250ms delay tap",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 295.0, 430.0, 250.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-29",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 530.0, 30.0, 30.0 ],
					"comment" : "audio out L"
				}
			},
			{
				"box" : 				{
					"id" : "obj-30",
					"maxclass" : "outlet",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 180.0, 530.0, 30.0, 30.0 ],
					"comment" : "audio out R"
				}
			},
			{
				"box" : 				{
					"id" : "obj-31",
					"maxclass" : "comment",
					"text" : "audio out L",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 65.0, 537.0, 90.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-32",
					"maxclass" : "comment",
					"text" : "audio out R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 215.0, 537.0, 90.0, 18.0 ]
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
					"source" : [ "obj-9", 0 ],
					"destination" : [ "obj-13", 0 ],
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
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-17", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-19", 0 ],
					"destination" : [ "obj-17", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-20", 0 ],
					"destination" : [ "obj-17", 3 ],
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
					"source" : [ "obj-17", 1 ],
					"destination" : [ "obj-25", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-24", 0 ],
					"destination" : [ "obj-26", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-25", 0 ],
					"destination" : [ "obj-27", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-26", 0 ],
					"destination" : [ "obj-29", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-27", 0 ],
					"destination" : [ "obj-30", 0 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
