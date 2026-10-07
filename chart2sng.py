#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (C) 2026 Sergio Gimenez
"""Turn a plain-text chord chart into a JJazzLab .sng song file.

Chart syntax: bars separated by "|", "%" repeats the previous bar,
several chords in one bar split it evenly ("C7 D7" = 2 beats each in 4/4).

    ./chart2sng.py "Gm | % | D7 | % | C7 | D7 | Gm | %" \
        --name GmBlues --tempo 80 --rhythm SlowBlues.S594.sst --choruses 8 -o GmBlues.sng
"""
import argparse
from pathlib import Path
from xml.sax.saxutils import quoteattr

VARIATIONS = ["Main A-1", "Main B-1", "Main C-1", "Main D-1"]


def parse_chart(chart: str, beats_per_bar: int = 4):
    """Return [(bar, beat, chord_name)] with consecutive duplicates dropped."""
    bars = [b.split() for b in chart.strip().strip("|").split("|")]
    events, prev_bar, last = [], None, None
    for i, bar in enumerate(bars):
        if bar == ["%"]:
            if prev_bar is None:
                raise ValueError("'%' in first bar")
            bar = prev_bar
        if not bar:
            raise ValueError(f"empty bar {i + 1}")
        step = beats_per_bar / len(bar)
        for j, chord in enumerate(bar):
            if chord != last:
                events.append((i, j * step, chord))
                last = chord
        prev_bar = bar
    return len(bars), events


def chord_xml(bar: int, beat: float, name: str) -> str:
    beat_s = f"{beat:g}"
    return f"""      <CLI__ChordSymbolImpl resolves-to="CLI_ChordSymbolSP">
        <spVERSION>3</spVERSION>
        <spChord resolves-to="ExtChordSymbolSP" spName={quoteattr(name)} spOriginalName={quoteattr(name)}>
          <spVERSION>3</spVERSION>
          <spRenderingInfo resolves-to="ChordRenderingInfoSP" serialization="custom">
            <ChordRenderingInfoSP>
              <int>3</int>
              <enum-set enum-type="Feature"></enum-set>
              <null/>
            </ChordRenderingInfoSP>
          </spRenderingInfo>
        </spChord>
        <spPos resolves-to="PositionSP" spVERSION="2" spPos="[{bar}:{beat_s}]"/>
        <spClientProperties>
          <owner class="CLI_ChordSymbolImpl" reference="../.."/>
        </spClientProperties>
      </CLI__ChordSymbolImpl>
"""


def song_part_xml(rhythm: str, start: int, nbars: int, section: str, chorus: int) -> str:
    variation = VARIATIONS[min(chorus // 2, len(VARIATIONS) - 1)]
    intensity = min(chorus // 2, 3)
    return f"""      <SongPartImpl resolves-to="SongPartImplSP" spRhythmId={quoteattr(rhythm + "-ID")} spRhythmTs="FOUR_FOUR" spStartBarIndex="{start}" spName={quoteattr(section)} spNbBars="{nbars}">
        <spVERSION>3</spVERSION>
        <spRhythmName>{rhythm}</spRhythmName>
        <spParentSection class="CLI_SectionImpl" reference="../../../../spChordLeadSheet/spItems/CLI__SectionImpl"/>
        <spClientProperties>
          <owner class="SongPartImpl" reference="../.."/>
        </spClientProperties>
        <spHashMapRpIdValue>
          <entry><string>rpVariationID</string><string>{variation}</string></entry>
          <entry><string>rpIntensityID</string><string>{intensity}</string></entry>
          <entry><string>rpSysMarkerID</string><string>solo</string></entry>
          <entry><string>RpFillID</string><string>always</string></entry>
          <entry><string>rpTempoID</string><string>100</string></entry>
        </spHashMapRpIdValue>
      </SongPartImpl>
"""


def build_song(chart, name, tempo, rhythm, choruses, section="A") -> str:
    nbars, events = parse_chart(chart)
    chords = "".join(chord_xml(*e) for e in events)
    parts = "".join(song_part_xml(rhythm, c * nbars, nbars, section, c) for c in range(choruses))
    return f"""<Song resolves-to="SongSP" spName={quoteattr(name)} spTempo="{tempo}">
  <spVERSION>4</spVERSION>
  <spComments>{chart}</spComments>
  <spTags/>
  <spChordLeadSheet class="ChordLeadSheetImpl" resolves-to="ChordLeadSheetImplSP">
    <spVERSION>2</spVERSION>
    <spItems>
      <CLI__SectionImpl resolves-to="CLI_SectionImplSP" spName={quoteattr(section)} spTs="FOUR_FOUR" spBarIndex="0">
        <spVERSION>3</spVERSION>
        <spClientProperties>
          <owner class="CLI_SectionImpl" reference="../.."/>
        </spClientProperties>
      </CLI__SectionImpl>
{chords}    </spItems>
    <spSize>{nbars}</spSize>
  </spChordLeadSheet>
  <spSongStructure class="SongStructureImpl" resolves-to="SongStructureImplSP">
    <spVERSION>2</spVERSION>
    <spSpts>
{parts}    </spSpts>
    <spParentCls class="ChordLeadSheetImpl" reference="../../spChordLeadSheet"/>
    <spKeepUpdated>true</spKeepUpdated>
  </spSongStructure>
  <spMapUserPhrases/>
  <spClientPropertiesV3>
    <properties/>
    <owner class="Song" reference="../.."/>
  </spClientPropertiesV3>
</Song>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chart")
    ap.add_argument("--name", default="Backing")
    ap.add_argument("--tempo", type=int, default=80)
    ap.add_argument("--rhythm", default="SlowBlues.S594.sst", help="style file name from ~/JJazzLab/Rhythms")
    ap.add_argument("--choruses", type=int, default=8)
    ap.add_argument("-o", "--output", type=Path)
    a = ap.parse_args()
    out = a.output or Path(f"{a.name}.sng")
    out.write_text(build_song(a.chart, a.name, a.tempo, a.rhythm, a.choruses))
    print(out)


if __name__ == "__main__":
    main()
