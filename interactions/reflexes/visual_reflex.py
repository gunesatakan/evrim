import pygame

def get_visual_reflex_direction(observer_pos, threat_pos, threat_direction):
    """
    Tehdit görüldüğünde (Görsel Refleks):
    Tehdidin gidiş yönüne dik (90 derece) olan en güvenli kaçış yönünü hesaplar.
    Observer, tehdidin merkezine göre hangi taraftaysa o tarafa doğru dik kaçar.
    
    Args:
        observer_pos (Vector2): Kaçacak olanın konumu.
        threat_pos (Vector2): Tehdidin konumu.
        threat_direction (Vector2): Tehdidin hareket yönü (normalize edilmiş olmalı).
        
    Returns:
        Vector2: Kaçış yönü vektörü (normalize).
    """
    # Tehdidin hareket yönü
    threat_dir = threat_direction.normalize() if threat_direction.length() > 0 else pygame.math.Vector2(1, 0)
    
    # Tehdide dik iki vektör (Sağ ve Sol)
    perp1 = pygame.math.Vector2(-threat_dir.y, threat_dir.x)
    perp2 = pygame.math.Vector2(threat_dir.y, -threat_dir.x)
    
    # Hangi yöne kaçmalı? 
    # Şu anki konumumuz tehdidin merkezine göre hangi taraftaysa o tarafa kaçalım.
    to_observer = observer_pos - threat_pos
    
    # Dot product ile hangi dik vektörün bize daha yakın (açısal olarak) olduğuna bakalım
    if to_observer.dot(perp1) > to_observer.dot(perp2):
        return perp1
    else:
        return perp2
