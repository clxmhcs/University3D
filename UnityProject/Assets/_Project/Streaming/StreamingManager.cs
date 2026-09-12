using UnityEngine;

namespace JiangchengUniversity.Streaming
{
    public sealed class StreamingManager : MonoBehaviour
    {
        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] StreamingManager initialized.");
        }
    }
}
