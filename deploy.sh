#!/usr/bin/env bash
cp binalerter.build     ~/.config/containers/systemd
cp binalerter.container ~/.config/containers/systemd
cp binalerter.timer     ~/.config/containers/systemd

systemctl --user daemon-reload
