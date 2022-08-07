# Led Matrix

## Polkit
Add the following to `/etc/polkit-1/localauthority/50-local.d/54-allow-poweroff.pkla`:

```
[Allow pi user to shutdown the system]
Identity=unix-user:*
Action=org.freedesktop.login1.set-wall-message;org.freedesktop.login1.power-off;org.freedesktop.login1.power-off-multiple-sessions;org.freedesktop.login1.power-off-ignore-inhibit
ResultAny=yes
ResultInactive=yes
ResultActive=yes
```

## Sudo
Add the following to `/etc/sudoers.d/daemon`:

```
daemon ALL=NOPASSWD: /bin/systemctl poweroff -i
```
