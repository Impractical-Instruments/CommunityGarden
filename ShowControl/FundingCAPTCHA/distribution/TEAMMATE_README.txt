=========================================================
 BodyCaptcha Level Editor -- Teammate Quick Start
=========================================================

WHAT THIS IS
------------
A tiny editor for building "select all squares containing X"
levels for the Funding CAPTCHA game.

GETTING STARTED
---------------
1. Unzip this folder somewhere on your computer (Desktop is fine).

2. In the images/ folder, create a SUBFOLDER named after
   yourself (lowercase, no spaces). Charlie will tell you what
   to call it -- usually just your first name.
   Examples:  images/alice/   images/bob/   images/charlie/

3. Drop your image files into YOUR subfolder.
   - .jpg, .jpeg, .png, and .webp all work.
   - Nested subfolders are fine (e.g. images/alice/animals/).

4. Double-click BodyCaptchaEditor.exe to launch the editor.
   - On first launch, Windows may warn about an unrecognized app.
     Click "More info" -> "Run anyway".

USING THE EDITOR
----------------
- PICK IMAGE in the sidebar -> choose an image for the current level.
- PROMPT (or press E) -> type the question text.
- Click cells in the grid to mark them as the "correct" answers.
- Use the +/- buttons to adjust difficulty, grid size, and timer.
- < PREV / NEXT > (or Left/Right arrows) -> navigate levels.
- + NEW LEVEL (or Ctrl+N) -> add a level.
- SAVE (or Ctrl+S) -> writes your work to bodycaptcha-levels.json
  next to the .exe. Do this often.

KEYBOARD SHORTCUTS
------------------
  E           edit the prompt text
  + / -       change difficulty
  Up / Down   change timer (+/- 5s)
  Left/Right  prev / next level
  Ctrl+S      save
  Ctrl+N      new level
  Ctrl+C      clear cell selections on the current level
  Ctrl+Del    delete the current level
  Esc         close the image picker

NOTES
-----
- If you add new images while the editor is open, close and
  reopen it so the picker re-scans the images folder.
- ONLY USE IMAGES IN YOUR OWN SUBFOLDER. If you reference an
  image outside your folder, your levels may conflict with
  someone else's when contributions are merged.

WHEN YOU'RE DONE
----------------
1. Hit SAVE one more time (just to be sure).
2. Close the editor.
3. Right-click the WHOLE folder -> "Send to" ->
   "Compressed (zipped) folder".
4. Email or upload that zip back to Charlie.

Thanks for contributing levels!
