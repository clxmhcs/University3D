using UnityEngine;

namespace JiangchengUniversity.Core
{
    public sealed class AudioManager : MonoBehaviour
    {
        private void Awake()
        {
            DontDestroyOnLoad(gameObject);
            Debug.Log("[Stage A] AudioManager initialized.");
        }
    }
}
