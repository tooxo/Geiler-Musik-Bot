#!/bin/sh
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo add-apt-repository -y ppa:projectatomic/ppa
sudo apt-get update
sudo apt-get -y -o Dpkg::Options::="--force-confnew" install docker-ce podman slirp4netns
pip install pytest python-coveralls docker-compose podman-compose pyyaml==3.13
pip install https://github.com/containers/podman-compose/archive/devel.tar.gz -U
docker-compose version
podman-compose version
{
  echo "BOT_TOKEN=$BOT_TOKEN"
  echo "MONGODB_URI=$MONGODB_URI"
  echo "MONGODB_DATABASE_NAME=$MONGODB_DATABASE_NAME"
  echo "SPOTIFY_ID=$SPOTIFY_ID"
  echo "SPOTIFY_SECRET=$SPOTIFY_SECRET"
  echo "TEST_ENVIRONMENT=True"
  echo "PORT=8001"
  echo "MONGO_ENABLED=False"
  echo "USE_EMBEDS=False"
} >> sysenv.env
touch youtube/settings.env
docker network create web
sudo apt-get install libopus0 python3-dev cython3 python-dev libopus-dev
git clone https://github.com/tooxo/distest.git --depth 1 -b develop
cd distest/ || exit
pip install -r requirements-dev.txt
pip install .
pip install pynacl cython
cd ..
sudo bash -c "echo [registries.search] > /etc/containers/registries.conf"
sudo bash -c 'echo registries = [\"docker.io\"] >> /etc/containers/registries.conf'
