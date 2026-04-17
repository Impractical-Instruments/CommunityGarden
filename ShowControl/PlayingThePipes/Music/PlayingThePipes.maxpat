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
		"rect" : [ 60, 60, 1280, 940 ],
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
		"description" : "Playing The Pipes — top-level music system. Receives OSC (8 encoders + 8 switches) from water-valve hardware. Drives: audio clip launcher, MIDI clip launcher + synths, 4-channel spatial output, fog machines, and LEDs.",
		"boxes" : [
			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "comment",
					"text" : "Playing The Pipes — Music System",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 15.0, 500.0, 28.0 ],
					"fontsize" : 18.0,
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-2",
					"maxclass" : "comment",
					"text" : "OSC input (8 encoders, 8 switches) → audio/MIDI clip launchers → synths → FX → 4-ch spatial output + fog/LED",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 47.0, 900.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-3",
					"maxclass" : "comment",
					"text" : "All abstractions live in the same folder as this patch. Open each to inspect or extend its internals.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 67.0, 800.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-4",
					"maxclass" : "comment",
					"text" : "── INPUT ──────────────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 100.0, 800.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-5",
					"maxclass" : "newobj",
					"text" : "pp.osc-in",
					"numinlets" : 0,
					"numoutlets" : 2,
					"outlettype" : [ "", "" ],
					"patching_rect" : [ 30.0, 125.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-6",
					"maxclass" : "comment",
					"text" : "outlet 0: encoder data [num 0.0-1.0]   outlet 1: switch data [num 0/1]",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 165.0, 129.0, 500.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "newobj",
					"text" : "unpack i f",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "float" ],
					"patching_rect" : [ 30.0, 165.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-8",
					"maxclass" : "newobj",
					"text" : "unpack i i",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 600.0, 165.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "comment",
					"text" : "encoder num + value",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 169.0, 160.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-10",
					"maxclass" : "comment",
					"text" : "switch num + state",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 700.0, 169.0, 160.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-11",
					"maxclass" : "comment",
					"text" : "── CLIP LAUNCHERS ─────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 210.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-12",
					"maxclass" : "comment",
					"text" : "Switches 1-4 trigger audio clips; switches 5-8 trigger MIDI clips.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 228.0, 600.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-13",
					"maxclass" : "newobj",
					"text" : "route 1 2 3 4",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "bang", "bang", "bang", "bang", "" ],
					"patching_rect" : [ 600.0, 248.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-14",
					"maxclass" : "comment",
					"text" : "route switch 1-4 to audio launcher",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 730.0, 252.0, 280.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "newobj",
					"text" : "route 5 6 7 8",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "bang", "bang", "bang", "bang", "" ],
					"patching_rect" : [ 600.0, 280.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "comment",
					"text" : "route switch 5-8 to MIDI launcher + fog",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 730.0, 284.0, 300.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "newobj",
					"text" : "pp.audio-clip-launcher",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "signal" ],
					"patching_rect" : [ 30.0, 265.0, 200.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-18",
					"maxclass" : "newobj",
					"text" : "pp.midi-clip-launcher",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "int", "int", "int" ],
					"patching_rect" : [ 350.0, 265.0, 195.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-19",
					"maxclass" : "comment",
					"text" : "outlet 0=L  outlet 1=R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 240.0, 269.0, 160.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-20",
					"maxclass" : "comment",
					"text" : "outlet 0=pitch  1=vel  2=gate",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 555.0, 269.0, 220.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-21",
					"maxclass" : "comment",
					"text" : "── SYNTHESIS ──────────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 315.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-22",
					"maxclass" : "comment",
					"text" : "Two synth voices fed by the MIDI clip launcher. Voice 2 is transposed up an octave (+12 semitones).",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 333.0, 700.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-23",
					"maxclass" : "newobj",
					"text" : "pp.synth",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "signal" ],
					"patching_rect" : [ 350.0, 358.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-24",
					"maxclass" : "newobj",
					"text" : "pp.synth",
					"numinlets" : 3,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "signal" ],
					"patching_rect" : [ 550.0, 358.0, 90.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-25",
					"maxclass" : "comment",
					"text" : "voice 1 (root)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 450.0, 362.0, 110.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-26",
					"maxclass" : "comment",
					"text" : "voice 2 (+1 octave)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 650.0, 362.0, 130.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-27",
					"maxclass" : "newobj",
					"text" : "+ 12",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"patching_rect" : [ 550.0, 335.0, 50.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-28",
					"maxclass" : "comment",
					"text" : "octave up for voice 2",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 610.0, 335.0, 160.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-29",
					"maxclass" : "comment",
					"text" : "── MIX BUS ────────────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 405.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-30",
					"maxclass" : "comment",
					"text" : "Sum all audio sources to a stereo bus, then send through the shared effects chain.",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 423.0, 700.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-31",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 448.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-32",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 90.0, 448.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-33",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 150.0, 448.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-34",
					"maxclass" : "comment",
					"text" : "L bus: audio clips + synth voices",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 452.0, 260.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-35",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 30.0, 480.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-36",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 90.0, 480.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-37",
					"maxclass" : "newobj",
					"text" : "+~",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "signal" ],
					"patching_rect" : [ 150.0, 480.0, 45.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-38",
					"maxclass" : "comment",
					"text" : "R bus",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 210.0, 484.0, 60.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-39",
					"maxclass" : "comment",
					"text" : "── EFFECTS ────────────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 520.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-40",
					"maxclass" : "newobj",
					"text" : "pp.fx-chain",
					"numinlets" : 2,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "signal" ],
					"patching_rect" : [ 30.0, 545.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-41",
					"maxclass" : "comment",
					"text" : "gain → HPF → reverb → delay",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 165.0, 549.0, 230.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-42",
					"maxclass" : "comment",
					"text" : "── SPATIAL OUTPUT + HARDWARE CONTROL ─────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 590.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-43",
					"maxclass" : "newobj",
					"text" : "pp.spatial-out",
					"numinlets" : 2,
					"numoutlets" : 4,
					"outlettype" : [ "signal", "signal", "signal", "signal" ],
					"patching_rect" : [ 30.0, 615.0, 135.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-44",
					"maxclass" : "comment",
					"text" : "Ch1=front-L  Ch2=front-R  Ch3=rear-L  Ch4=rear-R",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 180.0, 619.0, 380.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-45",
					"maxclass" : "newobj",
					"text" : "pp.fog-led",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 750.0, 615.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-46",
					"maxclass" : "comment",
					"text" : "inlet 0=fog trigger  inlet 1=LED level (encoder 8)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 880.0, 619.0, 380.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-47",
					"maxclass" : "newobj",
					"text" : "sel 8",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "" ],
					"patching_rect" : [ 700.0, 558.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-48",
					"maxclass" : "comment",
					"text" : "switch 8 → fog trigger",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 770.0, 562.0, 200.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-49",
					"maxclass" : "newobj",
					"text" : "sel 8",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "" ],
					"patching_rect" : [ 700.0, 590.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-50",
					"maxclass" : "comment",
					"text" : "encoder 8 → LED level",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 770.0, 594.0, 200.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-51",
					"maxclass" : "comment",
					"text" : "── AUDIO OUTPUT ───────────────────────────────────────────────────────────────",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 660.0, 900.0, 18.0 ],
					"fontface" : 1
				}
			},
			{
				"box" : 				{
					"id" : "obj-52",
					"maxclass" : "newobj",
					"text" : "dac~ 1 2 3 4",
					"numinlets" : 4,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 30.0, 685.0, 120.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-53",
					"maxclass" : "comment",
					"text" : "hardware channels 1-4  (front-L, front-R, rear-L, rear-R)",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 165.0, 689.0, 450.0, 18.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-54",
					"maxclass" : "newobj",
					"text" : "ezdac~",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 30.0, 720.0, 60.0, 22.0 ]
				}
			},
			{
				"box" : 				{
					"id" : "obj-55",
					"maxclass" : "comment",
					"text" : "ezdac~ shown here for development convenience — use dac~ 1 2 3 4 above in performance",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 100.0, 724.0, 700.0, 18.0 ]
				}
			}
		],
		"lines" : [
			{
				"patchline" : 				{
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-7", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-5", 1 ],
					"destination" : [ "obj-8", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-8", 0 ],
					"destination" : [ "obj-13", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-8", 0 ],
					"destination" : [ "obj-15", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-8", 0 ],
					"destination" : [ "obj-47", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-7", 0 ],
					"destination" : [ "obj-49", 0 ],
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
					"source" : [ "obj-13", 1 ],
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 2 ],
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-13", 3 ],
					"destination" : [ "obj-17", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-15", 0 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-15", 1 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-15", 2 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-15", 3 ],
					"destination" : [ "obj-18", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-23", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 1 ],
					"destination" : [ "obj-23", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 2 ],
					"destination" : [ "obj-23", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 0 ],
					"destination" : [ "obj-27", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-27", 0 ],
					"destination" : [ "obj-24", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 1 ],
					"destination" : [ "obj-24", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-18", 2 ],
					"destination" : [ "obj-24", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-17", 0 ],
					"destination" : [ "obj-31", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-23", 0 ],
					"destination" : [ "obj-31", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-31", 0 ],
					"destination" : [ "obj-33", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-24", 0 ],
					"destination" : [ "obj-32", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-32", 0 ],
					"destination" : [ "obj-33", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-17", 1 ],
					"destination" : [ "obj-35", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-23", 1 ],
					"destination" : [ "obj-35", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-35", 0 ],
					"destination" : [ "obj-37", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-24", 1 ],
					"destination" : [ "obj-36", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-36", 0 ],
					"destination" : [ "obj-37", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-33", 0 ],
					"destination" : [ "obj-40", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-37", 0 ],
					"destination" : [ "obj-40", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-40", 0 ],
					"destination" : [ "obj-43", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-40", 1 ],
					"destination" : [ "obj-43", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-43", 0 ],
					"destination" : [ "obj-52", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-43", 1 ],
					"destination" : [ "obj-52", 1 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-43", 2 ],
					"destination" : [ "obj-52", 2 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-43", 3 ],
					"destination" : [ "obj-52", 3 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-47", 0 ],
					"destination" : [ "obj-45", 0 ],
					"midpoints" : []
				}
			},
			{
				"patchline" : 				{
					"source" : [ "obj-49", 0 ],
					"destination" : [ "obj-45", 1 ],
					"midpoints" : []
				}
			}
		],
		"parameters" : {},
		"dependency_cache" : [],
		"autosave" : 0
	}
}
