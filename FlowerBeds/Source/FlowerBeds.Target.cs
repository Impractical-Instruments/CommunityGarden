using UnrealBuildTool;

public class FlowerBedsTarget : TargetRules
{
	public FlowerBedsTarget(TargetInfo target) : base(target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V6;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
		ExtraModuleNames.Add("FlowerBeds");
	}
}
