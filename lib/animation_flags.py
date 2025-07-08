
class OdinAnimationFlags:
    def __init__(self, flags = 0):
        self.flags = flags
        
    @property
    def has_frametime(self)-> bool:
        return self.flags & 1 != 0
    
    @property
    def has_rotation(self)-> bool:
        return self.flags & 2 != 0
        
    @property
    def has_translation(self) -> bool:
        return self.flags & 4 != 0
    
    @property
    def has_scale(self) -> bool:
        return self.flags & 8 != 0
    
    @property
    def has_separate_scale(self) -> bool:
        return self.flags & 16 != 0
    
    @property
    def elements_count(self) -> int:
        counter = 0
        if (self.has_frametime): counter += 1
        if (self.has_rotation): counter += 4
        if (self.has_translation): counter += 3
        if (self.has_separate_scale and self.has_scale):
            counter += 3
        elif (self.has_scale):
            counter += 1
            
        return counter