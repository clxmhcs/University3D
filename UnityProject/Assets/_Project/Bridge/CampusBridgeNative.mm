#import <Foundation/Foundation.h>

// Stage A native callback hook.
// The host Xcode project should replace the NSLog body with a call into
// the Swift-side CampusBridge receiver once UnityFramework is embedded.

extern "C" void CampusBridge_SendToSwift(const char *json)
{
    if (json == nullptr) {
        return;
    }

    NSString *message = [NSString stringWithUTF8String:json];
    NSLog(@"[CampusBridge][Unity→Swift native placeholder] %@", message);
}
