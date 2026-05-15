{
  mkShell,
  python314,
  uv,
  curl,
  docker,
  jq,
}:

mkShell {
  packages = [
    python314
    uv
    curl
    docker
    jq
  ];

  UV_PYTHON = "${python314}/bin/python3.14";
}
