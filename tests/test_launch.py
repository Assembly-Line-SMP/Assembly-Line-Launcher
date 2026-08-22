from pathlib import Path

from launcher.auth.models import Account, AccountType
from launcher.core.instance import Instance, InstanceMetadata
from launcher.core.launch import LaunchSettings, build_launch_command
from launcher.core.loader_installer import LoaderProfile
from launcher.core.vanilla_installer import VanillaVersionInfo


def test_launch_uses_minecraft_version_for_version_name(tmp_path):
    metadata = InstanceMetadata(
        id="test",
        name="Test",
        modrinth_version_id="pack-id",
        modrinth_version_number="2.3.1",
        minecraft_version="1.21.1",
        loader_id="neoforge",
        loader_version="21.1.248",
        java_major=21,
    )
    instance = Instance(tmp_path, metadata)
    vanilla = VanillaVersionInfo(
        version_id="1.21.1",
        client_jar=Path("client.jar"),
        main_class="net.minecraft.client.main.Main",
        libraries=[],
        natives_dir=tmp_path / "natives",
        asset_index_id="17",
        assets_dir=tmp_path / "assets",
        minecraft_arguments=None,
        game_arguments=[
            "--version", "${version_name}",
            "--width", "${resolution_width}",
            "--height", "${resolution_height}",
        ],
    )
    loader = LoaderProfile(
        main_class="cpw.mods.bootstraplauncher.BootstrapLauncher",
        extra_classpath=[],
        extra_game_arguments=["--launchTarget", "forgeclient", "--fml.mcVersion", "1.21.1"],
        extra_jvm_arguments=[],
        profile_id="neoforge-21.1.248",
    )
    account = Account(
        id="account",
        username="player",
        uuid="00000000-0000-0000-0000-000000000000",
        type=AccountType.CRACKED,
    )

    command = build_launch_command(
        Path("java"), instance, vanilla, loader, account, LaunchSettings()
    )

    assert command[command.index("--version") + 1] == "1.21.1"
    assert "-Dminecraft.api.auth.host=https://nope.invalid" in command
    assert command.count("--width") == 1
    assert command[command.index("--width") + 1] == "1280"
    assert command.count("--height") == 1
    assert command[command.index("--height") + 1] == "720"


def test_neoforge_launch_includes_loader_target_arguments(tmp_path):
    metadata = InstanceMetadata(
        id="test",
        name="Test",
        modrinth_version_id="pack-id",
        modrinth_version_number="2.3.1",
        minecraft_version="1.21.1",
        loader_id="neoforge",
        loader_version="21.1.248",
        java_major=21,
    )
    instance = Instance(tmp_path, metadata)
    vanilla = VanillaVersionInfo(
        version_id="1.21.1",
        client_jar=Path("client.jar"),
        main_class="net.minecraft.client.main.Main",
        libraries=[],
        natives_dir=tmp_path / "natives",
        asset_index_id="17",
        assets_dir=tmp_path / "assets",
        minecraft_arguments=None,
        game_arguments=[],
    )
    loader = LoaderProfile(
        main_class="cpw.mods.bootstraplauncher.BootstrapLauncher",
        extra_classpath=[],
        extra_game_arguments=[
            "--fml.neoForgeVersion", "21.1.248",
            "--fml.fmlVersion", "4.0.43",
            "--fml.mcVersion", "1.21.1",
            "--fml.neoFormVersion", "20240808.144430",
            "--launchTarget", "forgeclient",
        ],
        extra_jvm_arguments=[],
        profile_id="neoforge-21.1.248",
    )
    account = Account(
        id="account",
        username="player",
        uuid="00000000-0000-0000-0000-000000000000",
        type=AccountType.CRACKED,
    )

    command = build_launch_command(
        Path("java"), instance, vanilla, loader, account, LaunchSettings()
    )

    assert command[command.index("--launchTarget") + 1] == "forgeclient"
    assert command[command.index("--fml.mcVersion") + 1] == "1.21.1"
    assert command[command.index("--fml.neoForgeVersion") + 1] == "21.1.248"