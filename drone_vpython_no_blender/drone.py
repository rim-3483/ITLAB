from vpython import box, cylinder, vector

class Drone:
    def __init__(self, position):
        self.body=box(pos=position,size=vector(.34,.13,.34),color=vector(.9,.2,.22))
        self.arms=[box(pos=position,size=vector(.95,.06,.07),color=vector(.65,.7,.75)),
                   box(pos=position,size=vector(.07,.06,.95),color=vector(.65,.7,.75))]
        self.rotors=[]
        for dx in (-.45,.45):
            for dz in (-.45,.45):
                offset=vector(dx,.045,dz)
                rotor=cylinder(pos=position+offset,axis=vector(0,.018,0),
                               radius=.16,color=vector(.18,.55,.9),opacity=.65)
                self.rotors.append((rotor,offset))

    def move_to(self, position):
        self.body.pos=position
        for arm in self.arms: arm.pos=position
        for rotor,offset in self.rotors: rotor.pos=position+offset
