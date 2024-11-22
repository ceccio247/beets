# This file is part of beets.
# Copyright 2024, Rose Ceccio
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Converts fields with multiple artists (i.e. featured artists) to a separated list."""

import re

from beets import plugins, ui
from beets.util import displayable_path


def split_on_feat(artist):
    """Given an artist string, split all artists into an array"""
    # split on the first "feat".
    regex = re.compile(plugins.feat_tokens(), re.IGNORECASE)
    parts = [s.strip() for s in regex.split(artist)]
    return parts

class FtSeparatorPlugin(plugins.BeetsPlugin):
    def __init__(self):
        super().__init__()

        self.config.add(
            {
                "auto": True,
                "separator": "; ",
                "convert_album_artist": False,
                "convert_sort_artist": False,
            }
        )

        self._command = ui.Subcommand(
            "ftseparator", help="turn multi-artist fields into separated lists"
        )

        self._command.parser.add_option(
            "-s",
            "--separator",
            dest="separator",
            default="; ",
            help="separator to be inserted between each artist",
        )

        self._command.parser.add_option(
            "-a",
            "--albumartist",
            dest="convert_album_artist",
            default=None,
            action="store_true",
            help="apply conversion to album artist field",
        )
        self._command.parser.add_option(
            "-r",
            "--sortartist",
            dest="convert_sort_artist",
            default=None,
            action="store_true",
            help="apply conversion to sort artist field",
        )

        if self.config["auto"]:
            self.import_stages = [self.imported]

    def commands(self):
        def func(lib, opts, args):
            self.config.set_args(opts)
            separator = self.config["separator"].get()
            album = self.config["convert_album_artist"].get(bool)
            sort = self.config["convert_sort_artist"].get(bool)
            write = ui.should_write()

            for item in lib.items(ui.decargs(args)):
                self.ft_separate(item, separator, album, sort)
                item.store()
                if write:
                    item.try_write()

        self._command.func = func
        return [self._command]

    def imported(self, session, task):
        """Import hook for separating artist automatically."""
        separator = self.config["separator"].get()
        album = self.config["convert_album_artist"].get(bool)
        sort = self.config["convert_sort_artist"].get(bool)

        for item in task.imported_items():
            self.ft_separate(item, separator, album, sort)
            item.store()

    def ft_separate(self, item, separator, convert_album_artist, convert_sort_artist):
        """Generate artist lists and store them in appropriate tags"""
        artist = item.artist.strip()
        # we can do this because join only inserts between entries
        # if there is only one artist, no change takes place
        artist_list = separator.join(split_on_feat(artist))
        
        if artist_list != artist:
            self._log.info("artist: {0} -> {1}", item.artist, artist_list)
            item.artist = artist_list

        # perform much the same action for the album artists
        if convert_album_artist and item.albumartist:
            albumartist = item.albumartist.strip()
            albumartist_list = separator.join(split_on_feat(albumartist))
            if albumartist_list != albumartist:
                self._log.info("albumartist: {0} -> {1}", item.albumartist, albumartist_list)
                item.albumartist = albumartist_list

        if convert_sort_artist and item.artist_sort:
            artist_sort = item.artist_sort.strip()
            artist_sort_list = separator.join(split_on_feat(artist_sort))
            if artist_sort_list != artist_sort:
                self._log.info("artist_sort: {0} -> {1}", item.artist_sort, artist_sort_list)
                item.artist_sort = artist_sort_list

