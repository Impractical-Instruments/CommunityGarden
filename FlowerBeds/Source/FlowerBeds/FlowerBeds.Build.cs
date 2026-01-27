// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class FlowerBeds : ModuleRules
{
	public FlowerBeds(ReadOnlyTargetRules target) : base(target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(["Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput"]);
	}
}
