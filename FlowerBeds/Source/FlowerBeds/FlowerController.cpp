#include "FlowerController.h"

#include "OSCClient.h"
#include "OSCManager.h"

void UFlowerController::Init(const FFlowerControllerConfig& Config)
{
	OscClient = UOSCManager::CreateOSCClient(
		Config.IPAddress,
		Config.Port,
		"FlowerControllerOSCClient",
		this);
}

void UFlowerController::SendFlowerRotation(const FOSCAddress& Address, float Rotation) const
{
	UE::OSC::FOSCData RotationData(Rotation);
	FOSCMessage Message(Address, { RotationData });
	OscClient->SendOSCMessage(Message);
}
