Notes / caveats:

The Dockerfiles use addgroup/adduser (Debian-based images). If a build fails complaining about those commands, update the Dockerfiles to install adduser first via apt-get before creating the user.